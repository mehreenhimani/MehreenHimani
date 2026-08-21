"""
Routing tests — the governance logic.

Routing decides who may call what, at what cost, and where the call lands when a
region is down. Every one of those is a promise the platform makes to a tenant, so
each gets a test that would fail loudly if the promise were quietly changed.
"""

import pytest

from app.gateway.catalog import CATALOG, VIRTUAL_KEYS, resolve_model


def test_a_known_model_is_served_directly():
    d = resolve_model("carecopilot-balanced", virtual_key="sk-carecopilot-dev")
    assert d["selected"] == "carecopilot-balanced"
    assert not d["denied"]


def test_an_unknown_model_falls_back_to_the_default():
    d = resolve_model("gpt-9-ultra", virtual_key="sk-carecopilot-prod")
    assert d["selected"] == "carecopilot-balanced"
    assert any("not in catalogue" in r for r in d["reasons"])


def test_entitlement_is_enforced_not_advisory():
    """The dev key is not entitled to the deep tier and must not receive it."""
    d = resolve_model("carecopilot-deep", virtual_key="sk-carecopilot-dev")
    assert d["selected"] != "carecopilot-deep"
    assert d["selected"] in VIRTUAL_KEYS["sk-carecopilot-dev"].allowed_models
    assert any("not entitled" in r for r in d["reasons"])


def test_an_unknown_key_is_denied_outright():
    d = resolve_model("carecopilot-fast", virtual_key="sk-does-not-exist")
    assert d["denied"]
    assert d["selected"] is None


def test_a_trivial_turn_is_downshifted_to_the_cheap_tier():
    d = resolve_model(
        "carecopilot-balanced", virtual_key="sk-carecopilot-prod", complexity="trivial"
    )
    assert d["selected"] == "carecopilot-fast"


def test_a_complex_turn_is_upshifted_to_the_deep_tier():
    d = resolve_model("carecopilot-fast", virtual_key="sk-carecopilot-prod", complexity="complex")
    assert d["selected"] == "carecopilot-deep"


def test_downshifting_never_overrides_entitlement():
    """A cheap tier is still a tier a key may be forbidden from using."""
    d = resolve_model("carecopilot-fast", virtual_key="sk-marketing-dev", complexity="complex")
    assert d["selected"] in VIRTUAL_KEYS["sk-marketing-dev"].allowed_models


def test_an_unhealthy_deployment_fails_over_within_the_data_zone():
    d = resolve_model(
        "carecopilot-balanced",
        virtual_key="sk-carecopilot-prod",
        unhealthy=frozenset({"carecopilot-balanced"}),
    )
    assert d["selected"] == "carecopilot-balanced-westeu"
    assert CATALOG[d["selected"]].data_zone == "eu"


def test_failover_chains_more_than_one_hop():
    d = resolve_model(
        "carecopilot-balanced",
        virtual_key="sk-carecopilot-prod",
        unhealthy=frozenset({"carecopilot-balanced", "carecopilot-balanced-westeu"}),
    )
    assert d["selected"] == "carecopilot-deep"


def test_failover_terminates_when_everything_is_unhealthy():
    """A routing loop under a total outage would be worse than the outage."""
    d = resolve_model(
        "carecopilot-balanced", virtual_key="sk-carecopilot-prod", unhealthy=frozenset(CATALOG)
    )
    assert d["selected"] in CATALOG


def test_cost_attribution_rides_on_the_key():
    d = resolve_model("carecopilot-fast", virtual_key="sk-marketing-dev")
    assert d["cost_centre"] == "cc-8802-growth"
    assert d["tenant"] == "growth-marketing"


@pytest.mark.parametrize("name,entry", CATALOG.items())
def test_every_model_is_in_an_eu_data_zone(name, entry):
    """Data residency is a contract with the DPO, so it gets a test, not a comment."""
    assert entry.data_zone == "eu", f"{name} is outside the EU data zone"


@pytest.mark.parametrize("name,entry", CATALOG.items())
def test_every_fallback_target_exists(name, entry):
    for target in entry.fallbacks:
        assert target in CATALOG, f"{name} falls back to unknown model '{target}'"


def test_cost_maths_matches_the_published_price():
    entry = CATALOG["carecopilot-balanced"]
    # 1M in + 1M out at $2.50 + $10.00
    assert entry.cost_usd(1_000_000, 1_000_000) == pytest.approx(12.50)
