# =====================================================================================
# Redcare Agentic AI Platform — Azure baseline policy.
#
# Evaluated against `terraform show -json`. Each rule states the resource, what is
# wrong, and implicitly why: the message is what a developer reads at 5pm, so it has
# to be actionable on its own.
# =====================================================================================
package terraform.plan

import rego.v1

# --- helpers -------------------------------------------------------------------------
resources[r] if {
	some change in input.resource_changes
	not "delete" in change.change.actions
	r := {
		"address": change.address,
		"type": change.type,
		"values": object.get(change.change, "after", {}),
	}
}

by_type(t) := [r | some r in resources; r.type == t]

# Data residency: health data under GDPR Art. 9 does not leave the EU. This is the
# one rule that is a reportable breach rather than a finding.
allowed_regions := {"swedencentral", "westeurope", "germanywestcentral", "northeurope"}

# =====================================================================================
# Data residency
# =====================================================================================
deny contains msg if {
	some r in resources
	region := object.get(r.values, "location", "")
	region != ""
	not region in allowed_regions
	msg := sprintf(
		"%s is in region '%s'. Health-data workloads are EU-only: %v",
		[r.address, region, allowed_regions],
	)
}

# =====================================================================================
# Network exposure
# =====================================================================================
private_only_types := {
	"azurerm_cognitive_account",
	"azurerm_key_vault",
	"azurerm_search_service",
	"azurerm_storage_account",
	"azurerm_redis_cache",
	"azurerm_postgresql_flexible_server",
	"azurerm_container_registry",
}

deny contains msg if {
	some r in resources
	r.type in private_only_types
	object.get(r.values, "public_network_access_enabled", false) == true
	not startswith(r.address, "module.dev")
	msg := sprintf(
		"%s has public network access enabled. Reach it over a private endpoint instead — the blast radius of a leaked credential should be nothing.",
		[r.address],
	)
}

deny contains msg if {
	some r in by_type("azurerm_storage_account")
	object.get(r.values, "allow_nested_items_to_be_public", true) == true
	msg := sprintf("%s allows public blobs. Set allow_nested_items_to_be_public = false.", [r.address])
}

# =====================================================================================
# Identity and secrets
# =====================================================================================
deny contains msg if {
	some r in by_type("azurerm_container_registry")
	object.get(r.values, "admin_enabled", false) == true
	msg := sprintf(
		"%s has the admin account enabled. That is a shared password with no owner and no rotation; use managed identity and AcrPull.",
		[r.address],
	)
}

deny contains msg if {
	some r in by_type("azurerm_cognitive_account")
	object.get(r.values, "local_auth_enabled", true) == true
	msg := sprintf(
		"%s allows key-based auth. Set local_auth_enabled = false so the only way in is Entra ID.",
		[r.address],
	)
}

deny contains msg if {
	some r in by_type("azurerm_postgresql_flexible_server")
	some auth in object.get(r.values, "authentication", [])
	object.get(auth, "password_auth_enabled", true) == true
	msg := sprintf(
		"%s permits password authentication. Managed identity only — the moment one password exists it ends up in a runbook.",
		[r.address],
	)
}

deny contains msg if {
	some r in by_type("azurerm_key_vault")
	object.get(r.values, "purge_protection_enabled", false) == false
	msg := sprintf(
		"%s has purge protection disabled, so a deleted vault is unrecoverable. This is the control an auditor asks about first.",
		[r.address],
	)
}

deny contains msg if {
	some r in by_type("azurerm_key_vault")
	object.get(r.values, "enable_rbac_authorization", false) == false
	msg := sprintf(
		"%s uses legacy access policies. RBAC keeps Key Vault access in the same review as every other permission.",
		[r.address],
	)
}

# A literal secret in a plan is a secret in state, and state outlives the mistake.
deny contains msg if {
	some r in by_type("azurerm_key_vault_secret")
	value := object.get(r.values, "value", "")
	value != ""
	value != "PLACEHOLDER-SET-OUT-OF-BAND"
	msg := sprintf(
		"%s carries a literal secret value. Terraform state is not a secret store; create the slot and set the value out of band.",
		[r.address],
	)
}

# =====================================================================================
# Reliability
# =====================================================================================
# The gateway is on the critical path of every AI call in the company. A cold start
# here presents as a timeout, which looks like an application bug for twenty minutes.
deny contains msg if {
	some r in by_type("azurerm_container_app")
	contains(object.get(r.values, "name", ""), "litellm")
	some t in object.get(r.values, "template", [])
	object.get(t, "min_replicas", 0) < 1
	msg := sprintf("%s scales the AI gateway to zero. Every AI feature in the company waits on a cold start.", [r.address])
}

deny contains msg if {
	some r in by_type("azurerm_container_app")
	some t in object.get(r.values, "template", [])
	count(object.get(t, "container", [])) > 0
	some c in t.container
	count(object.get(c, "liveness_probe", [])) == 0
	msg := sprintf("%s has no liveness probe, so a wedged replica keeps taking traffic.", [r.address])
}

# =====================================================================================
# Responsible AI
# =====================================================================================
deny contains msg if {
	some r in by_type("azurerm_cognitive_deployment")
	object.get(r.values, "rai_policy_name", "") == ""
	msg := sprintf(
		"%s deploys a model with no responsible-AI policy attached. Content filtering is not optional on a customer-facing surface.",
		[r.address],
	)
}

# =====================================================================================
# Governance metadata — untagged spend is unattributable spend
# =====================================================================================
required_tags := {"platform", "environment", "owner", "cost_centre", "data_classification"}

taggable_types := {
	"azurerm_resource_group",
	"azurerm_key_vault",
	"azurerm_storage_account",
	"azurerm_cognitive_account",
	"azurerm_container_app",
	"azurerm_search_service",
	"azurerm_postgresql_flexible_server",
	"azurerm_redis_cache",
	"azurerm_container_registry",
}

deny contains msg if {
	some r in resources
	r.type in taggable_types
	tags := object.get(r.values, "tags", {})
	missing := required_tags - {k | some k, _ in tags}
	count(missing) > 0
	msg := sprintf("%s is missing required tags %v. Untagged spend cannot be charged back and unclassified data cannot be governed.", [r.address, missing])
}

# =====================================================================================
# Warnings — reviewed, not blocking
# =====================================================================================
warn contains msg if {
	some r in by_type("azurerm_postgresql_flexible_server")
	object.get(r.values, "backup_retention_days", 0) < 14
	msg := sprintf("%s keeps fewer than 14 days of backups. Fine for dev; ask whether it is fine for the spend ledger.", [r.address])
}

warn contains msg if {
	some r in by_type("azurerm_log_analytics_workspace")
	object.get(r.values, "daily_quota_gb", -1) == -1
	msg := sprintf("%s has no daily ingestion cap, so a log storm becomes a budget event.", [r.address])
}
