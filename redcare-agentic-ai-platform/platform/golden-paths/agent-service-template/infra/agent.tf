# =====================================================================================
# Onboarding a new agent onto the platform.
#
# This is the entire infrastructure change. Everything else — networking, identity,
# secrets, the gateway, observability, the pipeline — already exists and is owned by
# the platform team. Copy this block into infra/terraform/envs/<env>/main.tf inside
# the `agents` map and open a pull request.
#
# If onboarding ever needs more than this, the platform has a gap; that is the
# signal the platform team watches for.
# =====================================================================================

# "my-agent" = {
#   tenant      = "my-team"                 # appears on every metric, log and spend line
#   cost_centre = "cc-XXXX-my-team"         # required: unattributable spend is not allowed
#   image_tag   = var.agent_image_tag       # CD supplies the commit SHA
#   external    = false                     # true only if customers reach it directly
#
#   min_replicas = 1                        # 0 is fine in dev, never in prod
#   max_replicas = 10
#   cpu          = 0.5
#   memory       = "1Gi"
#   concurrent_requests_per_replica = 30
#
#   # FinOps. The gateway enforces this; the app mirrors it so a runaway loop stops
#   # itself before the gateway has to.
#   daily_budget_usd = 50
#
#   # Governance. Both are required by policy — see platform/policies/agent_onboarding.rego.
#   hitl_enabled        = true              # must be true if the tier is high-risk
#   eu_ai_act_risk_tier = "limited-risk"    # minimal-risk | limited-risk | high-risk
#
#   # Progressive delivery.
#   canary_percentage      = 10
#   stable_revision_suffix = var.stable_revision_suffix
#
#   key_vault_secret_uris = {
#     "my-agent-virtual-key" = module.security.secret_uris["my-agent-virtual-key"]
#   }
# }
