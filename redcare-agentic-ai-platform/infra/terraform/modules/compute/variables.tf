variable "resource_group_name" { type = string }
variable "environment" { type = string }

variable "container_app_environment_id" { type = string }
variable "agent_identity_id" { type = string }
variable "agent_client_id" { type = string }
variable "gateway_base_url" { type = string }
variable "otel_endpoint" {
  type    = string
  default = ""
}
variable "service_bus_namespace" {
  type    = string
  default = ""
}

variable "container_registry_login_server" {
  type        = string
  description = "Shared registry from the runtime module."
}

variable "agents" {
  type = map(object({
    tenant                          = string
    cost_centre                     = string
    image_tag                       = string
    external                        = bool
    min_replicas                    = number
    max_replicas                    = number
    cpu                             = number
    memory                          = string
    concurrent_requests_per_replica = number
    daily_budget_usd                = number
    hitl_enabled                    = bool
    eu_ai_act_risk_tier             = string
    canary_percentage               = number
    stable_revision_suffix          = string
    key_vault_secret_uris           = map(string)
    queue_name                      = optional(string)
  }))
  description = <<-DESC
    Every agent on the platform, as data. Onboarding a new team is an entry here plus
    a repo from the golden-path template — not a new pipeline and not a platform-team
    project. This map is the platform's adoption surface.
  DESC
}

variable "tags" { type = map(string) }
