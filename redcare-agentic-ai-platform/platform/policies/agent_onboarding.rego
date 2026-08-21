# =====================================================================================
# Agent onboarding policy.
#
# Every agent joining the platform declares itself in the `agents` map of the compute
# module. These rules are the platform's admission criteria: what a team must be able
# to say about their agent before it may run in production. They are deliberately
# short — an onboarding checklist nobody can memorise is an onboarding checklist
# people route around.
# =====================================================================================
package terraform.plan

import rego.v1

agent_apps[r] if {
	some change in input.resource_changes
	change.type == "azurerm_container_app"
	not "delete" in change.change.actions
	values := object.get(change.change, "after", {})
	not contains(object.get(values, "name", ""), "litellm")
	r := {"address": change.address, "values": values}
}

env_map(values) := m if {
	m := {e.name: object.get(e, "value", "") |
		some t in object.get(values, "template", [])
		some c in object.get(t, "container", [])
		some e in object.get(c, "env", [])
	}
}

# Rule 1 — every agent goes through the gateway. This is the one that makes every
# other platform guarantee enforceable rather than advisory.
deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "LITELLM_BASE_URL", "") == ""
	msg := sprintf("%s does not point at the AI gateway. Direct provider access bypasses entitlement, budgets, failover, caching and cost attribution all at once.", [r.address])
}

deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "LLM_MODE", "") != "litellm"
	msg := sprintf("%s is not running in gateway mode. Set LLM_MODE=litellm outside local development.", [r.address])
}

# Rule 2 — guardrails are the platform's, not the tenant's, and cannot be opted out of.
deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "GUARDRAILS_ENABLED", "true") == "false"
	msg := sprintf("%s disables guardrails. Injection defence, PII redaction and output policy are platform-level controls.", [r.address])
}

# Rule 3 — spend must be attributable and capped.
deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "COST_CENTRE", "") == ""
	msg := sprintf("%s declares no cost centre, so its spend cannot be charged back to anyone.", [r.address])
}

deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "BUDGET_TENANT_DAILY_USD", "") == ""
	msg := sprintf("%s has no daily budget. An agent loop with no ceiling is an unbounded invoice.", [r.address])
}

# Rule 4 — the EU AI Act risk tier is a decision someone has to make on the record.
valid_risk_tiers := {"minimal-risk", "limited-risk", "high-risk"}

deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	tier := object.get(env, "EU_AI_ACT_RISK_TIER", "")
	not tier in valid_risk_tiers
	msg := sprintf("%s declares risk tier '%s'. Classify it as one of %v — an unclassified AI system cannot be signed off.", [r.address, tier, valid_risk_tiers])
}

# Rule 5 — a high-risk agent must keep a human in the loop. EU AI Act Art. 14.
deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "EU_AI_ACT_RISK_TIER", "") == "high-risk"
	object.get(env, "HITL_ENABLED", "false") != "true"
	msg := sprintf("%s is classified high-risk with human-in-the-loop disabled. Art. 14 requires effective human oversight.", [r.address])
}

# Rule 6 — production never runs a mutable tag. "Which code is running?" must have
# exactly one answer.
deny contains msg if {
	some r in agent_apps
	env := env_map(r.values)
	object.get(env, "ENVIRONMENT", "") == "prod"
	some t in object.get(r.values, "template", [])
	some c in object.get(t, "container", [])
	endswith(object.get(c, "image", ""), ":latest")
	msg := sprintf("%s runs the ':latest' tag in production. Pin the image digest so the running revision is identifiable.", [r.address])
}
