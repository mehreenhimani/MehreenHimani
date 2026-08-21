variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "private_endpoint_subnet_id" { type = string }
variable "key_vault_dns_zone_id" { type = string }

variable "secret_names" {
  type = list(string)
  default = [
    "azure-openai-sweden-key",
    "azure-openai-westeu-key",
    "anthropic-api-key",
    "litellm-master-key",
    "litellm-salt-key",
    "litellm-database-url",
    "redis-password",
    "content-safety-key",
    "carecopilot-virtual-key",
  ]
  description = "Secret slots the platform expects. Values are set out of band."
}

variable "enable_defender" {
  type        = bool
  default     = true
  description = "Defender plans cost money; dev may run without them."
}

variable "tags" { type = map(string) }
