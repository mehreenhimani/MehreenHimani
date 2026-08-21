variable "subscription_id" { type = string }

variable "location" {
  type    = string
  default = "swedencentral"
}

variable "github_repo" {
  type        = string
  default     = "redcare/agentic-ai-platform"
  description = "owner/repo — the OIDC subject is built from it."
}

variable "agent_image_tag" {
  type        = string
  default     = "latest"
  description = "CD passes the immutable commit SHA; 'latest' is a dev convenience only."
}

variable "otel_endpoint" {
  type    = string
  default = "http://otel-collector:4317"
}

variable "config_storage_account_name" { type = string }
variable "config_storage_access_key" {
  type      = string
  sensitive = true
}

variable "oncall_emails" {
  type    = list(string)
  default = ["ai-platform-dev@redcare.example"]
}
