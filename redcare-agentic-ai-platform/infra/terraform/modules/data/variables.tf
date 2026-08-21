variable "name_prefix" { type = string }
variable "resource_group_name" { type = string }
variable "tenant_id" { type = string }

variable "primary_location" { type = string }
variable "secondary_location" {
  type    = string
  default = "westeurope"
}
variable "enable_secondary_region" {
  type        = bool
  default     = true
  description = "Second Azure OpenAI region for failover and extra quota."
}
variable "secondary_capacity_ratio" {
  type    = number
  default = 0.5
}

variable "model_deployments" {
  type = map(object({
    model_name             = string
    model_version          = string
    sku_name               = string
    capacity_tpm_thousands = number
    rai_policy             = string
  }))
  description = <<-DESC
    Model deployments as data. capacity is in thousands of tokens per minute, and it
    is the number that decides both throughput and bill — treat a change to it as a
    funding decision, which is why it lives in a reviewed file.
  DESC
  default = {
    "gpt-4o-mini" = {
      model_name             = "gpt-4o-mini"
      model_version          = "2024-07-18"
      sku_name               = "GlobalStandard"
      capacity_tpm_thousands = 200
      rai_policy             = "redcare-strict"
    }
    "gpt-4o" = {
      model_name             = "gpt-4o"
      model_version          = "2024-11-20"
      sku_name               = "GlobalStandard"
      capacity_tpm_thousands = 100
      rai_policy             = "redcare-strict"
    }
    "text-embedding-3-large" = {
      model_name             = "text-embedding-3-large"
      model_version          = "1"
      sku_name               = "Standard"
      capacity_tpm_thousands = 120
      rai_policy             = "redcare-strict"
    }
  }
}

variable "private_endpoint_subnet_id" { type = string }
variable "data_subnet_id" { type = string }
variable "openai_dns_zone_id" { type = string }
variable "search_dns_zone_id" { type = string }
variable "postgres_dns_zone_id" { type = string }
variable "redis_dns_zone_id" { type = string }

variable "cmk_key_vault_key_id" {
  type    = string
  default = null
}
variable "cmk_identity_client_id" {
  type    = string
  default = null
}

variable "search_sku" {
  type    = string
  default = "standard"
}
variable "search_replicas" {
  type    = number
  default = 1
}
variable "search_partitions" {
  type    = number
  default = 1
}
variable "search_semantic_sku" {
  type    = string
  default = "free"
}

variable "storage_replication" {
  type    = string
  default = "ZRS"
}

variable "postgres_sku" {
  type    = string
  default = "GP_Standard_D2ds_v5"
}
variable "postgres_storage_mb" {
  type    = number
  default = 32768
}
variable "postgres_backup_days" {
  type    = number
  default = 7
}
variable "postgres_geo_backup" {
  type    = bool
  default = false
}
variable "postgres_ha" {
  type    = bool
  default = false
}

variable "redis_capacity" {
  type    = number
  default = 1
}
variable "redis_family" {
  type    = string
  default = "C"
}
variable "redis_sku" {
  type    = string
  default = "Standard"
}

variable "tags" { type = map(string) }
