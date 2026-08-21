variable "resource_group_name" { type = string }

variable "container_app_environment_id" {
  type        = string
  description = "Shared Container Apps environment from the runtime module."
}
variable "gateway_config_storage_name" {
  type        = string
  description = "Named storage mount carrying config.yaml, created by the runtime module."
}
variable "gateway_identity_id" { type = string }
variable "gateway_client_id" { type = string }
variable "container_registry_login_server" { type = string }

variable "litellm_image" {
  type    = string
  default = "ghcr.io/berriai/litellm:main-stable"
}

variable "key_vault_secret_uris" {
  type        = map(string)
  description = "secret name -> Key Vault versionless secret URI. Values never enter Terraform."
  default     = {}
}

variable "openai_primary_endpoint" { type = string }
variable "openai_secondary_endpoint" {
  type    = string
  default = ""
}
variable "content_safety_endpoint" { type = string }
variable "redis_hostname" { type = string }
variable "otel_endpoint" {
  type    = string
  default = ""
}


variable "min_replicas" {
  type        = number
  default     = 2
  description = "Never 0. The gateway is on the critical path of every AI call in the company."
  validation {
    condition     = var.min_replicas >= 1
    error_message = "The gateway must not scale to zero."
  }
}
variable "max_replicas" {
  type    = number
  default = 10
}
variable "cpu" {
  type    = number
  default = 1.0
}
variable "memory" {
  type    = string
  default = "2Gi"
}
variable "concurrent_requests_per_replica" {
  type    = number
  default = 60
}

variable "tags" { type = map(string) }
