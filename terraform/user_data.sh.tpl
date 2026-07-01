#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Bootstrap for Todozee Past-Life (FastAPI + local Gemma 4 LLM, GPU)
# Rendered by Terraform (templatefile). Bash variable braces are written
# doubled (double-dollar brace) so Terraform passes them through;
# single-dollar brace values are Terraform-injected from the resource.
#
# Base image: AWS Deep Learning Base GPU AMI (Ubuntu 22.04) — NVIDIA
# driver + CUDA already present, so we only install a CUDA torch build.
# The app requires Python 3.13 (pyproject requires-python >=3.13), which
# we install from the deadsnakes PPA since the AMI ships 3.10.
# ─────────────────────────────────────────────────────────────────────
set -euxo pipefail
exec > >(tee -a /var/log/bootstrap.log) 2>&1
echo "=== bootstrap start $(date -u) ==="

export DEBIAN_FRONTEND=noninteractive
export HOME=/root

APP_DIR=/opt/${project_name}
REPO_DIR=$${APP_DIR}/repo
VENV_DIR=$${APP_DIR}/venv
HF_HOME_DIR=$${APP_DIR}/hf-cache
CACHE_DIR=$${APP_DIR}/model-cache
LOG_DIR=$${REPO_DIR}/logs

mkdir -p "$${APP_DIR}" "$${HF_HOME_DIR}" "$${CACHE_DIR}"

# ── 0. Confirm the GPU is visible (fail loud if the AMI/driver is wrong) ─
nvidia-smi || { echo "ERROR: nvidia-smi failed — no GPU/driver."; exit 1; }

# ── 1. System packages + Python 3.13 (deadsnakes) ─────────────────────
apt-get update -y
apt-get install -y --no-install-recommends software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y --no-install-recommends \
  git curl ca-certificates gnupg unzip jq build-essential \
  python3.13 python3.13-venv python3.13-dev \
  libglib2.0-0 libgl1

# ── 2. AWS CLI v2 (CloudWatch agent config fetch helper; harmless if present) ─
if ! command -v aws >/dev/null 2>&1; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscli.zip
  unzip -q /tmp/awscli.zip -d /tmp
  /tmp/aws/install --update
  rm -rf /tmp/awscli.zip /tmp/aws
fi

# ── 3. Clone the application ──────────────────────────────────────────
git config --system --add safe.directory "$${REPO_DIR}" || true
git clone "${repo_url}" "$${REPO_DIR}"
git -C "$${REPO_DIR}" checkout "${git_ref}"
mkdir -p "$${LOG_DIR}"

# ── 4. Python 3.13 venv + CUDA torch + app deps ───────────────────────
python3.13 -m venv "$${VENV_DIR}"
"$${VENV_DIR}/bin/pip" install --upgrade pip wheel setuptools

# GPU torch. PyPI default already ships a CUDA build on linux-x86_64 that
# runs on the A10G (sm_86). torch_cuda_index pins a specific wheel index.
TORCH_INDEX="${torch_cuda_index}"
if [ -n "$${TORCH_INDEX}" ]; then
  "$${VENV_DIR}/bin/pip" install --index-url "$${TORCH_INDEX}" torch torchvision
else
  "$${VENV_DIR}/bin/pip" install torch torchvision
fi

# transformers>=5.0, accelerate, kerykeion, pyswisseph, fastapi, etc.
# (torch already satisfied above -> not reinstalled)
"$${VENV_DIR}/bin/pip" install -r "$${REPO_DIR}/requirements.txt"

# Fail loud if torch can't see the GPU (we provisioned a GPU box on purpose).
"$${VENV_DIR}/bin/python" - <<'PYCHECK'
import torch, sys
assert torch.cuda.is_available(), "CUDA not available to torch after install"
print("torch", torch.__version__, "CUDA OK:", torch.cuda.get_device_name(0))
PYCHECK

# ── 5. App environment file ───────────────────────────────────────────
ENV_FILE=$${APP_DIR}/app.env
cat > "$${ENV_FILE}" <<EOF
HF_HOME=$${HF_HOME_DIR}
XDG_CACHE_HOME=$${CACHE_DIR}
LOG_FILE=$${LOG_DIR}/app.log
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
TOKENIZERS_PARALLELISM=false
HF_TOKEN=${hf_token}
EOF
chmod 600 "$${ENV_FILE}"

# Everything under APP_DIR owned by the service user
chown -R ubuntu:ubuntu "$${APP_DIR}"

# ── 6. systemd service ────────────────────────────────────────────────
# Past_Life.py preloads the model at startup (first boot downloads ~10GB),
# so give it unlimited start time.
cat > /etc/systemd/system/${project_name}.service <<EOF
[Unit]
Description=Todozee Past-Life (FastAPI + local Gemma 4 LLM, GPU)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$${REPO_DIR}
EnvironmentFile=$${ENV_FILE}
ExecStart=$${VENV_DIR}/bin/python Past_Life.py --host 0.0.0.0 --port ${app_port}
Restart=on-failure
RestartSec=10
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${project_name}.service
systemctl start ${project_name}.service

# ── 6b. Co-hosted Palm-Reader service (consolidated onto this box) ─────
# Palm-Reader shares this A10G. It targets Python 3.10 (the AMI default),
# so — unlike the app above — it does NOT use the deadsnakes 3.13 venv.
# Gated by palmreader_enabled so this box can be built without it.
if [ "${palmreader_enabled}" = "true" ]; then
  echo "=== provisioning co-hosted Palm-Reader ==="
  PR_APP_DIR=/opt/${palmreader_project_name}
  PR_REPO_DIR=$${PR_APP_DIR}/repo
  PR_VENV_DIR=$${PR_APP_DIR}/venv
  PR_HF_HOME=$${PR_APP_DIR}/hf-cache
  PR_CACHE=$${PR_APP_DIR}/model-cache
  PR_LOG_DIR=$${PR_REPO_DIR}/logs
  PR_STORAGE_DIR=$${PR_REPO_DIR}/request_logs

  mkdir -p "$${PR_APP_DIR}" "$${PR_HF_HOME}" "$${PR_CACHE}"

  git config --system --add safe.directory "$${PR_REPO_DIR}" || true
  git clone "${palmreader_repo_url}" "$${PR_REPO_DIR}"
  git -C "$${PR_REPO_DIR}" checkout "${palmreader_git_ref}"
  mkdir -p "$${PR_LOG_DIR}" "$${PR_STORAGE_DIR}"

  python3.10 -m venv "$${PR_VENV_DIR}"
  "$${PR_VENV_DIR}/bin/pip" install --upgrade pip wheel setuptools
  TORCH_INDEX="${torch_cuda_index}"
  if [ -n "$${TORCH_INDEX}" ]; then
    "$${PR_VENV_DIR}/bin/pip" install --index-url "$${TORCH_INDEX}" torch torchvision
  else
    "$${PR_VENV_DIR}/bin/pip" install torch torchvision
  fi
  if [ -f "$${PR_REPO_DIR}/requirements.lock.txt" ]; then
    "$${PR_VENV_DIR}/bin/pip" install -r "$${PR_REPO_DIR}/requirements.lock.txt"
  else
    "$${PR_VENV_DIR}/bin/pip" install -r "$${PR_REPO_DIR}/requirements.txt"
  fi

  cat > "$${PR_APP_DIR}/app.env" <<PRENV
API_PORT=${palmreader_app_port}
MODEL_ID=google/gemma-4-E2B-it
LOG_DIR=$${PR_LOG_DIR}
STORAGE_DIR=$${PR_STORAGE_DIR}
HF_HOME=$${PR_HF_HOME}
XDG_CACHE_HOME=$${PR_CACHE}
PYTHONUNBUFFERED=1
TOKENIZERS_PARALLELISM=false
HF_TOKEN=${palmreader_hf_token}
PRENV
  chmod 600 "$${PR_APP_DIR}/app.env"
  chown -R ubuntu:ubuntu "$${PR_APP_DIR}"

  cat > /etc/systemd/system/${palmreader_project_name}.service <<PRUNIT
[Unit]
Description=Todozee Palm-Reader (FastAPI + local Gemma 4 E2B, GPU)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$${PR_REPO_DIR}
EnvironmentFile=$${PR_APP_DIR}/app.env
ExecStart=$${PR_VENV_DIR}/bin/python palm_astrology_api.py
Restart=on-failure
RestartSec=10
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
PRUNIT

  systemctl daemon-reload
  systemctl enable ${palmreader_project_name}.service
  systemctl start ${palmreader_project_name}.service

  # Authorize the Palm-Reader CI/CD deploy key so its own GitHub Actions
  # pipeline can SSH-deploy to this shared box (its private key is the
  # Palm-Reader repo's EC2_SSH_KEY secret; EC2_HOST points at this EIP).
  install -d -m 700 -o ubuntu -g ubuntu /home/ubuntu/.ssh
  PR_AK=/home/ubuntu/.ssh/authorized_keys
  touch "$${PR_AK}"
  if ! grep -qF "${palmreader_deploy_public_key}" "$${PR_AK}"; then
    echo "${palmreader_deploy_public_key}" >> "$${PR_AK}"
  fi
  chown ubuntu:ubuntu "$${PR_AK}"; chmod 600 "$${PR_AK}"
fi

# ── 7. Caddy reverse proxy (auto-HTTPS) ───────────────────────────────
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

cat > /etc/caddy/Caddyfile <<EOF
{
    email ${acme_email}
}

${domain} {
    encode zstd gzip
    reverse_proxy 127.0.0.1:${app_port}
}
EOF

# Second vhost for the co-hosted Palm-Reader (larger body limit for palm
# image uploads). Appended only when Palm-Reader is enabled.
if [ "${palmreader_enabled}" = "true" ]; then
  cat >> /etc/caddy/Caddyfile <<EOF

${palmreader_domain} {
    encode zstd gzip
    request_body {
        max_size ${palmreader_max_body}
    }
    reverse_proxy 127.0.0.1:${palmreader_app_port}
}
EOF
fi

systemctl enable caddy
systemctl restart caddy

# ── 8. CloudWatch agent (memory + disk + GPU metrics, bootstrap+app logs) ─
curl -fsSL "https://amazoncloudwatch-agent-${region}.s3.${region}.amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb" \
  -o /tmp/cwagent.deb || \
  curl -fsSL "https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb" \
  -o /tmp/cwagent.deb
dpkg -i -E /tmp/cwagent.deb || true
rm -f /tmp/cwagent.deb

# Quoted heredoc: bash performs no expansion. Terraform still renders
# project_name before the script runs; the doubled-dollar InstanceId
# token below stays literal for the CloudWatch agent to resolve.
cat > /opt/aws/amazon-cloudwatch-agent/etc/cw-config.json <<'EOF'
{
  "agent": { "metrics_collection_interval": 60 },
  "metrics": {
    "namespace": "TodozeePastLife",
    "append_dimensions": { "InstanceId": "$${aws:InstanceId}" },
    "metrics_collected": {
      "mem": { "measurement": ["mem_used_percent"] },
      "disk": { "measurement": ["used_percent"], "resources": ["/"] },
      "nvidia_gpu": {
        "measurement": [
          "utilization_gpu",
          "memory_used",
          "memory_total",
          "temperature_gpu"
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/bootstrap.log",
            "log_group_name": "/${project_name}/bootstrap",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/opt/${project_name}/repo/logs/app.log",
            "log_group_name": "/${project_name}/app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/cw-config.json || true

echo "=== bootstrap finished $(date -u) ==="
