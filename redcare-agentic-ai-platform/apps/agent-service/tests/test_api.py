"""
API contract tests.

The /platform/* endpoints are the internal developer experience this platform sells.
If they drift, the internal catalogue and the playground both lie, so their shape is
tested like any other public contract.
"""


def test_health_and_readiness_are_separate_signals(client):
    assert client.get("/healthz").json()["status"] == "ok"
    ready = client.get("/readyz").json()
    assert ready["ready"] is True
    assert set(ready["checks"]) == {"tools_registered", "catalog_loaded", "gateway"}


def test_metrics_are_exposed_in_prometheus_format(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    for family in (
        "agent_requests_total",
        "llm_cost_usd_total",
        "guardrail_firings_total",
        "agent_tool_calls_total",
    ):
        assert family in body, f"missing metric family {family}"


def test_a_chat_turn_returns_a_full_decision_trace(client):
    r = client.post("/v1/chat", json={"message": "Where is my order RC10045821?"})
    assert r.status_code == 200
    body = r.json()
    for field in (
        "reply",
        "session_id",
        "trace_id",
        "model_used",
        "routing",
        "steps",
        "guardrails",
        "tool_calls",
        "cost_usd",
        "stop_reason",
    ):
        assert field in body, f"missing field {field}"
    assert body["routing"]["selected"]
    assert body["trace"]["spans"]


def test_the_model_catalogue_publishes_price_and_region(client):
    models = client.get("/platform/catalog").json()["models"]
    assert models
    for m in models:
        assert m["region"] and m["upstream_model"]
        assert m["input_usd_per_mtok"] >= 0


def test_virtual_keys_publish_their_governance_metadata(client):
    keys = client.get("/platform/keys").json()["keys"]
    for k in keys:
        assert k["owner_group"] and k["cost_centre"]
        assert k["daily_budget_usd"] > 0
        assert k["budget_remaining_usd"] <= k["daily_budget_usd"]


def test_every_tool_declares_its_blast_radius(client):
    tools = client.get("/platform/tools").json()["tools"]
    assert tools
    for t in tools:
        assert t["owner"] and t["data_classification"]
        # Anything that changes a system of record must be gated on a human.
        if t["side_effect"]:
            assert t["requires_approval"], f"{t['name']} mutates state without a gate"


def test_governance_posture_is_served_as_data(client):
    g = client.get("/platform/governance").json()
    assert g["eu_ai_act"]["risk_tier"]
    assert len(g["eu_ai_act"]["obligations"]) >= 4
    assert all(o["status"] == "met" for o in g["eu_ai_act"]["obligations"])
    assert "EU only" in g["gdpr"]["data_residency"]


def test_the_effective_config_never_leaks_a_secret(client):
    c = client.get("/platform/config").json()
    assert c["virtual_key"].endswith("…"), "the virtual key must be truncated"
    blob = str(c).lower()
    for forbidden in ("password", "secret=", "api_key", "bearer"):
        assert forbidden not in blob


def test_the_approval_flow_is_end_to_end(client):
    turn = client.post("/v1/chat", json={"message": "Can I take ibuprofen with warfarin?"}).json()
    approval_id = turn["pending_approval"]["approval_id"]

    pending = client.get("/v1/approvals").json()["pending"]
    assert any(p["approval_id"] == approval_id for p in pending)

    decided = client.post(
        f"/v1/approvals/{approval_id}",
        json={"approve": True, "actor": "pharmacist@redcare.example"},
    ).json()
    assert decided["approval"]["status"] == "approved"
    assert decided["executed"]["ticket_id"].startswith("PHARM-")

    # A decision is final: the same approval cannot be replayed.
    assert client.post(f"/v1/approvals/{approval_id}", json={"approve": True}).status_code == 404


def test_chaos_toggling_changes_the_routing_decision(client):
    client.post("/platform/chaos", json={"model": "carecopilot-balanced", "unhealthy": True})
    turn = client.post(
        "/v1/chat",
        json={"message": "Do you have paracetamol in stock?", "virtual_key": "sk-carecopilot-prod"},
    ).json()
    assert turn["model_used"] == "carecopilot-balanced-westeu"
    client.post("/platform/chaos", json={"model": "carecopilot-balanced", "unhealthy": False})


def test_chaos_rejects_an_unknown_model(client):
    assert (
        client.post("/platform/chaos", json={"model": "nope", "unhealthy": True}).status_code == 404
    )


def test_the_audit_log_records_every_turn(client):
    client.post("/v1/chat", json={"message": "Where is my order RC10045821?"})
    entries = client.get("/platform/audit").json()["entries"]
    completed = [e for e in entries if e["event"] == "turn_completed"]
    assert completed
    assert {"trace_id", "tenant", "model", "cost_usd", "actor"} <= set(completed[0])


def test_the_eval_gate_runs_and_reports(client):
    r = client.post("/platform/evals/run").json()
    assert r["cases"] == len(client.get("/platform/evals/cases").json()["cases"])
    assert set(r["gate"]) == {"task_success", "safety", "groundedness", "efficiency", "pass_rate"}
    assert r["gate_passed"] is True


def test_the_playground_is_served(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
