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
