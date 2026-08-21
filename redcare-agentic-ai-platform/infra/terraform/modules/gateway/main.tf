# =====================================================================================
# The AI gateway — LiteLLM on Azure Container Apps.
#
# The Container App itself; the environment and registry it sits on come from the
# runtime module. This is the single most important workload in the platform, because
# it is the only path from any workload to any model. Everything the platform promises about cost
# control, entitlement, failover and auditability is enforced here, so it gets the
# treatment a tier-1 service gets: internal ingress only, minimum two replicas, its
# own identity, its own database, its own alert set.
#
# Config is mounted from the repo rather than baked into the image, so a routing or
# budget change ships as a pull request against `gateway/litellm/config.yaml` and a
# revision restart, not a rebuild.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

resource "azurerm_container_app" "litellm" {
  name                         = "ca-litellm-gateway"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.gateway_identity_id]
  }

  registry {
    server   = var.container_registry_login_server
    identity = var.gateway_identity_id
  }

  # Secrets are Key Vault *references*: the platform resolves them at start-up using
  # the managed identity. The value never appears in Terraform state, in the image,
  # in a pipeline log, or in `az containerapp show`.
  dynamic "secret" {
    for_each = var.key_vault_secret_uris
    content {
      name                = secret.key
      key_vault_secret_id = secret.value
      identity            = var.gateway_identity_id
    }
  }

  ingress {
    external_enabled = false # only reachable from inside the VNet
    target_port      = 4000
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas # never zero: a cold gateway is an outage for everyone
    max_replicas = var.max_replicas

    container {
      name   = "litellm"
      image  = var.litellm_image
      cpu    = var.cpu
      memory = var.memory

      env {
        name  = "LITELLM_CONFIG_PATH"
        value = "/app/config/config.yaml"
      }
      env {
        name  = "PORT"
        value = "4000"
      }
      env {
        name  = "AZURE_OPENAI_SWEDEN_ENDPOINT"
        value = var.openai_primary_endpoint
      }
      env {
        name  = "AZURE_OPENAI_WESTEU_ENDPOINT"
        value = var.openai_secondary_endpoint
      }
      env {
        name  = "AZURE_CONTENT_SAFETY_ENDPOINT"
        value = var.content_safety_endpoint
      }
      env {
        name  = "REDIS_HOST"
        value = var.redis_hostname
      }
      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = var.otel_endpoint
      }
      env {
        name  = "OTEL_SERVICE_NAME"
        value = "litellm-gateway"
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = var.gateway_client_id
      }

      dynamic "env" {
        for_each = var.key_vault_secret_uris
        content {
          name        = upper(replace(env.key, "-", "_"))
          secret_name = env.key
        }
      }

      liveness_probe {
        transport = "HTTP"
        port      = 4000
        path      = "/health/liveliness"
        # Generous: restarting a healthy gateway under load makes an incident worse.
        initial_delay           = 30
        interval_seconds        = 30
        failure_count_threshold = 5
      }

      readiness_probe {
        transport               = "HTTP"
        port                    = 4000
        path                    = "/health/readiness"
        interval_seconds        = 10
        failure_count_threshold = 3
      }

      volume_mounts {
        name = "gateway-config"
        path = "/app/config"
      }
    }

    volume {
      name         = "gateway-config"
      storage_type = "AzureFile"
      storage_name = var.gateway_config_storage_name
    }

    # Scale on concurrent HTTP work, not CPU: an LLM proxy is IO-bound, so CPU stays
    # flat while the queue grows and a CPU rule would never fire.
    http_scale_rule {
      name                = "http-concurrency"
      concurrent_requests = var.concurrent_requests_per_replica
    }
  }

  lifecycle { ignore_changes = [template[0].container[0].image] } # image comes from CD
}
