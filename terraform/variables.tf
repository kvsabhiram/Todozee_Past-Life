variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1" # Mumbai
}

variable "project_name" {
  description = "Short name used to tag and name resources."
  type        = string
  default     = "todozee-past-life"
}

variable "instance_type" {
  description = "EC2 instance type. Gemma 4 local LLM inference -> g5.xlarge (NVIDIA A10G 24GB, 4 vCPU / 16 GB)."
  type        = string
  default     = "g5.xlarge"
}

variable "root_volume_gb" {
  description = "Root EBS volume size in GB. DLAMI base snapshot is ~75GB; leave headroom for CUDA torch + the ~10GB Gemma 4 weights in the HF cache + logs/storage."
  type        = number
  default     = 120
}

variable "domain" {
  description = "Public hostname Caddy serves with auto-HTTPS."
  type        = string
  default     = "pastlife.chatbucket.chat"
}

variable "acme_email" {
  description = "Email used by Caddy/Let's Encrypt for ACME registration."
  type        = string
  default     = "udathak@gmail.com"
}

variable "repo_url" {
  description = "Git repository cloned onto the instance."
  type        = string
  default     = "https://github.com/kvsabhiram/Todozee_Past-Life.git"
}

variable "git_ref" {
  description = "Git branch/tag/commit to check out."
  type        = string
  default     = "main"
}

variable "app_port" {
  description = "Port the FastAPI/uvicorn app listens on (see Past_Life.py / past_life.api)."
  type        = number
  default     = 7002
}

variable "torch_cuda_index" {
  description = "Optional PyTorch wheel index override. Empty = PyPI default, which already ships a CUDA build on Linux x86_64 (matched to the DLAMI driver, runs on the A10G's sm_86). Set e.g. https://download.pytorch.org/whl/cu128 to pin."
  type        = string
  default     = ""
}

variable "hf_token" {
  description = "Optional Hugging Face token. google/gemma-4-E2B-it is currently UNGATED so this is not required; leave empty. Provide only if the model later becomes gated or to avoid anonymous rate limits."
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to reach SSH (port 22). Lock this down to your IP for production."
  type        = string
  default     = "0.0.0.0/0"
}

variable "log_retention_days" {
  description = "Retention (in days) for the CloudWatch log groups the CW agent ships to. Keeps storage cost bounded."
  type        = number
  default     = 30
}

# ─── Alerting (SNS + GPU-memory alarm) ────────────────────────────────
variable "alarm_email" {
  description = "Email subscribed to the alarm SNS topic. Must be confirmed via the AWS email link (Terraform can't auto-confirm). Set to \"\" to skip the email subscription."
  type        = string
  default     = "udathak@gmail.com"
}

variable "gpu_memory_alarm_threshold_mib" {
  description = "Fire the GPU-memory alarm above this many MiB used. A10G total is ~23028 MiB; 22000 leaves ~1GB before CUDA OOM."
  type        = number
  default     = 22000
}

variable "gpu_name" {
  description = "GPU 'name' dimension the CloudWatch agent publishes (must match the instance_type's GPU). g5.xlarge = NVIDIA A10G."
  type        = string
  default     = "NVIDIA A10G"
}

variable "gpu_arch" {
  description = "GPU 'arch' dimension published by the CloudWatch agent. A10G = Ampere."
  type        = string
  default     = "Ampere"
}

# ─────────────────────────────────────────────────────────────────────
# Co-hosted Palm-Reader service (consolidated onto this same GPU box).
# Palm-Reader was merged onto the Past-Life box to share one A10G. These
# variables let the bootstrap also provision the Palm-Reader app (its own
# venv, systemd unit, Caddy vhost) so the consolidated box is fully
# reproducible from Terraform. Set palmreader_enabled=false to opt out.
# NOTE: Palm-Reader targets Python 3.10 (the AMI default), unlike this
# repo's own app which uses 3.13.
# ─────────────────────────────────────────────────────────────────────
variable "palmreader_enabled" {
  description = "Whether to also provision the co-hosted Palm-Reader service on this box."
  type        = bool
  default     = true
}

variable "palmreader_project_name" {
  description = "Name used for the Palm-Reader app dir (/opt/<name>) and systemd unit (<name>.service)."
  type        = string
  default     = "todozee-palm-reader"
}

variable "palmreader_repo_url" {
  description = "Palm-Reader git repository cloned onto the instance."
  type        = string
  default     = "https://github.com/kvsabhiram/Todozee_Palm-Reader.git"
}

variable "palmreader_git_ref" {
  description = "Palm-Reader git branch/tag/commit to check out."
  type        = string
  default     = "main"
}

variable "palmreader_domain" {
  description = "Public hostname Caddy serves for Palm-Reader with auto-HTTPS."
  type        = string
  default     = "palmreader.chatbucket.chat"
}

variable "palmreader_app_port" {
  description = "Port the Palm-Reader FastAPI app listens on (its app.env API_PORT)."
  type        = number
  default     = 7003
}

variable "palmreader_max_body" {
  description = "Caddy request_body max_size for Palm-Reader (palm image uploads)."
  type        = string
  default     = "25MB"
}

variable "palmreader_hf_token" {
  description = "Optional Hugging Face token for Palm-Reader. gemma-4-E2B-it is UNGATED so leave empty."
  type        = string
  default     = ""
  sensitive   = true
}

variable "palmreader_deploy_public_key" {
  description = "SSH public key for the Palm-Reader CI/CD deploy pipeline (added to ubuntu's authorized_keys so its GitHub Actions can SSH-deploy to this box). Keep the matching private key as the Palm-Reader repo's EC2_SSH_KEY secret."
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFe4hvtETq2glkBc1ZB6WgaJszVG7Fu+ZO18aUweCOtv palmreader-cicd-pastlife"
}
