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
  description = "Immutable image tag — the commit SHA. There is no 'latest' in production."
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
  default = ["ai-platform-oncall@redcare.example", "sre-oncall@redcare.example"]
}

variable "stable_revision_suffix" {
  type        = string
  description = "Revision suffix currently serving stable traffic; CD supplies it during a canary."
  default     = ""
}

variable "slack_webhook_url" {
  type      = string
  default   = null
  sensitive = true
}
