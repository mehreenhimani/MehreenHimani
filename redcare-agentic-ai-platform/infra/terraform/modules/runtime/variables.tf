variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "apps_subnet_id" { type = string }
variable "log_analytics_workspace_id" { type = string }

variable "internal_only" {
  type    = bool
  default = true
}
variable "zone_redundant" {
  type    = bool
  default = false
}

variable "acr_sku" {
  type    = string
  default = "Premium"
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "acr_sku must be Basic, Standard or Premium."
  }
}
variable "acr_public_access" {
  type    = bool
  default = false
}

variable "config_storage_account_name" { type = string }
variable "config_file_share_name" {
  type    = string
  default = "litellm-config"
}
variable "config_storage_access_key" {
  type      = string
  sensitive = true
}

variable "tags" { type = map(string) }
