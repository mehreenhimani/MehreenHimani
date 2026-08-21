variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "resource_group_id" { type = string }
variable "subscription_scope" { type = string }

variable "operational_retention_days" {
  type    = number
  default = 90
}
variable "audit_retention_days" {
  type        = number
  default     = 2555 # ~7 years; EU AI Act Art. 12 plus pharmacy record-keeping
  description = "Total retention for the AgentAudit table, archive tier included."
}
variable "daily_quota_gb" {
  type    = number
  default = 10
}
variable "trace_sampling_percentage" {
  type        = number
  default     = 100
  description = "Sample below 100 only when volume forces it — a sampled trace is a missing trace."
}

variable "enable_grafana" {
  type    = bool
  default = true
}
variable "grafana_public_access" {
  type    = bool
  default = false
}
variable "zone_redundant" {
  type    = bool
  default = false
}

variable "oncall_emails" {
  type    = list(string)
  default = ["ai-platform-oncall@redcare.example"]
}
variable "slack_webhook_url" {
  type      = string
  default   = null
  sensitive = true
}

variable "daily_budget_usd" {
  type    = number
  default = 900
}
variable "monthly_budget_eur" {
  type    = number
  default = 20000
}
variable "budget_start_date" {
  type    = string
  default = "2026-09-01T00:00:00Z"
}

variable "tags" { type = map(string) }
