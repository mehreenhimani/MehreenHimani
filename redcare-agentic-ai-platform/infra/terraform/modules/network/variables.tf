variable "name_prefix" {
  type        = string
  description = "Short prefix, e.g. raap-dev-sc."
}

variable "location" {
  type        = string
  description = "Azure region. EU only for health-data workloads."
  validation {
    condition     = contains(["swedencentral", "westeurope", "germanywestcentral", "northeurope"], var.location)
    error_message = "Data residency policy: EU regions only."
  }
}

variable "resource_group_name" { type = string }

variable "address_space" {
  type        = string
  description = "VNet CIDR, /16 recommended."
  default     = "10.42.0.0/16"
}

variable "ingress_source_prefix" {
  type        = string
  description = "Where HTTPS ingress may originate — an Application Gateway subnet in prod."
  default     = "VirtualNetwork"
}

variable "tags" { type = map(string) }
