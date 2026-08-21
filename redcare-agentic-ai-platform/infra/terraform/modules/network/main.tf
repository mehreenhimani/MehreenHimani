# =====================================================================================
# Network — the perimeter.
#
# The design rule: nothing in the AI plane is reachable from the public internet, and
# nothing in the AI plane reaches the public internet unobserved. Model calls, secret
# reads, database traffic and search queries all travel over private endpoints inside
# the VNet. For a workload handling health data this is not hardening, it is the
# baseline a data protection officer signs.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = [var.address_space]
  tags                = var.tags
}

# Container Apps needs a delegated subnet with a /23 or larger.
resource "azurerm_subnet" "apps" {
  name                 = "snet-apps"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [cidrsubnet(var.address_space, 7, 0)] # /23 out of a /16

  delegation {
    name = "container-apps"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Every PaaS dependency lands here as a private endpoint NIC.
resource "azurerm_subnet" "private_endpoints" {
  name                              = "snet-private-endpoints"
  resource_group_name               = var.resource_group_name
  virtual_network_name              = azurerm_virtual_network.main.name
  address_prefixes                  = [cidrsubnet(var.address_space, 8, 4)] # /24
  private_endpoint_network_policies = "Enabled"
}

resource "azurerm_subnet" "data" {
  name                 = "snet-data"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [cidrsubnet(var.address_space, 8, 5)]
  service_endpoints    = ["Microsoft.Storage", "Microsoft.KeyVault"]

  delegation {
    name = "postgres"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Deny-by-default at the subnet edge. The Container Apps platform needs its own
# inbound rules; everything else is explicit.
resource "azurerm_network_security_group" "apps" {
  name                = "nsg-${var.name_prefix}-apps"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  security_rule {
    name                       = "allow-https-from-appgw"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = var.ingress_source_prefix
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-vnet-internal"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  security_rule {
    name                       = "deny-all-inbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Egress: a compromised agent must not be able to post a customer record to an
  # arbitrary host. Outbound is allowed to Azure services and denied elsewhere.
  security_rule {
    name                       = "allow-egress-azure-services"
    priority                   = 200
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "AzureCloud"
  }

  security_rule {
    name                       = "deny-all-outbound-internet"
    priority                   = 4096
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }
}

resource "azurerm_subnet_network_security_group_association" "apps" {
  subnet_id                 = azurerm_subnet.apps.id
  network_security_group_id = azurerm_network_security_group.apps.id
}

# Private DNS: without these zones a private endpoint resolves to its public IP and
# the traffic silently leaves the VNet. This is the single most commonly missed
# control in an Azure private-networking design.
locals {
  private_dns_zones = {
    keyvault = "privatelink.vaultcore.azure.net"
    openai   = "privatelink.openai.azure.com"
    postgres = "privatelink.postgres.database.azure.com"
    redis    = "privatelink.redis.cache.windows.net"
    search   = "privatelink.search.windows.net"
    blob     = "privatelink.blob.core.windows.net"
    acr      = "privatelink.azurecr.io"
    monitor  = "privatelink.monitor.azure.com"
  }
}

resource "azurerm_private_dns_zone" "zones" {
  for_each            = local.private_dns_zones
  name                = each.value
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "links" {
  for_each              = azurerm_private_dns_zone.zones
  name                  = "link-${each.key}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = each.value.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false
  tags                  = var.tags
}
