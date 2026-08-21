# Infrastructure as Code

Everything Azure-side that the Agentic AI Platform runs on, expressed as Terraform.

## Why every resource is in here

A platform whose environments were partly clicked into the portal cannot answer the
two questions that matter most in an incident: *what changed?* and *is staging the
same as production?* Terraform makes the answer to the first a Git diff and the
answer to the second a shared module with different variables.

## Layout

```
modules/
  network/        VNet, subnets, private DNS zones, NSGs      — the perimeter
  identity/       managed identities, RBAC, OIDC federation   — who may do what
  security/       Key Vault, secrets, Content Safety          — where secrets live
  gateway/        LiteLLM Container App, Postgres, Redis      — the AI gateway
  compute/        agent Container App, ACR, autoscale         — where agents run
  data/           AI Search, Storage, Azure OpenAI deployments — the data/AI plane
  observability/  Log Analytics, App Insights, Grafana, alerts — how we see it
envs/
  dev/            small, permissive, scale-to-zero, cheap
  prod/           zone-redundant, private-only, budgeted, alerting
```

## The state backend

Remote state in an Azure Storage account with blob leasing for locking, one
container per environment, versioning and soft-delete on. State holds resource ids
and occasionally secret material, so the account is private-endpoint only and
readable by the deployment identity alone.

Bootstrap once with `scripts/bootstrap-tfstate.sh` — the state backend cannot be
managed by the state it stores.

## How a change reaches production

1. Open a PR. `terraform-plan.yml` runs `fmt`, `validate`, `plan`, Checkov, tfsec
   and Conftest, and posts the plan as a PR comment.
2. A human reads the plan. The diff is the review artefact.
3. Merge to `main`. `terraform-apply.yml` applies to dev automatically.
4. Production apply waits on a GitHub Environment protection rule — two approvers,
   and the saved plan file from the PR is what gets applied, so nothing drifts
   between review and apply.

No one has standing write access to the Azure subscriptions. GitHub authenticates
by OIDC federation and receives a short-lived token scoped to one environment.
