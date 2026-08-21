"""
The CareCopilot tool surface.

In production each handler is a thin, typed client over a real system of record
(SAP order management, the WMS, the ABDA/DACON drug database, the policy index in
Azure AI Search, ServiceNow). Here they are backed by deterministic fixtures so
the whole platform runs offline — but the *contract* is the production contract:
same names, same schemas, same failure shapes, same governance metadata.
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

from app.tools.registry import ToolSpec, registry

# --- fixtures -----------------------------------------------------------------------
_ORDERS = {
    "RC10045821": {
        "status": "in_transit",
        "carrier": "DHL",
        "days": 1,
        "items": ["Ibuprofen 400mg x20", "Vitamin D3 1000IU x60"],
        "value_eur": 24.80,
        "prescription": False,
    },
    "RC10045822": {
        "status": "awaiting_prescription",
        "carrier": "-",
        "days": None,
        "items": ["Metformin 850mg x100"],
        "value_eur": 18.20,
        "prescription": True,
    },
    "RC10045823": {
        "status": "delivered",
        "carrier": "DPD",
        "days": -3,
        "items": ["Omeprazole 20mg x30"],
        "value_eur": 11.40,
        "prescription": True,
    },
    "RC10045824": {
        "status": "returned",
        "carrier": "Hermes",
        "days": -1,
        "items": ["Blood pressure monitor"],
        "value_eur": 59.00,
        "prescription": False,
    },
}

_STOCK = {
    "ibuprofen": (1420, "in_stock", "same day"),
    "paracetamol": (86, "low_stock", "1-2 days"),
    "amoxicillin": (0, "out_of_stock", "restock 2026-09-04"),
    "vitamin d": (3300, "in_stock", "same day"),
    "metformin": (640, "in_stock", "same day"),
    "warfarin": (95, "low_stock", "1-2 days"),
    "omeprazole": (770, "in_stock", "same day"),
    "sertraline": (210, "in_stock", "same day"),
    "insulin": (48, "low_stock", "cold chain, 2 days"),
    "simvastatin": (410, "in_stock", "same day"),
    "aspirin": (2100, "in_stock", "same day"),
}

# Deliberately conservative pairs. A real deployment reads ABDA/DACON, and the
# platform pins the dataset version so an answer is reproducible months later.
_INTERACTIONS = {
    frozenset({"ibuprofen", "warfarin"}): (
        "HIGH_RISK",
        "NSAIDs markedly increase bleeding risk with vitamin-K antagonists.",
    ),
    frozenset({"aspirin", "warfarin"}): (
        "HIGH_RISK",
        "Additive antiplatelet and anticoagulant effect — bleeding risk.",
    ),
    frozenset({"ibuprofen", "aspirin"}): (
        "MODERATE_RISK",
        "Ibuprofen can blunt the cardioprotective effect of low-dose aspirin.",
    ),
    frozenset({"sertraline", "ibuprofen"}): (
        "MODERATE_RISK",
        "SSRI plus NSAID raises gastrointestinal bleeding risk.",
    ),
    frozenset({"metformin", "omeprazole"}): (
        "LOW_RISK",
        "Minor absorption interaction; clinically rarely significant.",
    ),
    frozenset({"simvastatin", "amoxicillin"}): ("LOW_RISK", "No significant interaction expected."),
}

_POLICIES = [
    {
        "id": "POL-RET-014",
        "title": "Returns of non-prescription products",
        "source": "Redcare Returns Policy v7 §3.2",
        "body": (
            "Unopened non-prescription products may be returned within 14 days of "
            "delivery for a full refund. Medicines that require cold-chain storage "
            "and opened hygiene products are excluded for safety reasons."
        ),
    },
    {
        "id": "POL-RET-021",
        "title": "Returns of prescription medicines",
        "source": "AMG §47 / Redcare Returns Policy v7 §4.1",
        "body": (
            "Prescription-only medicines cannot be returned once dispatched, except "
            "where the product is defective or was dispatched in error. German "
            "pharmaceutical law prohibits re-entry into the supply chain."
        ),
    },
    {
        "id": "POL-RX-003",
        "title": "Electronic prescriptions (E-Rezept)",
        "source": "Redcare Prescription Handling v3 §2",
        "body": (
            "An E-Rezept token must be redeemed through the gematik TI before the "
            "order can be released. Orders wait in 'awaiting_prescription' for up to "
            "28 days, after which they are cancelled and any pre-authorisation released."
        ),
    },
    {
        "id": "POL-GDPR-009",
        "title": "Health data handling and erasure",
        "source": "GDPR Art. 9 / Art. 17, Redcare DPA v4",
        "body": (
            "Order and medication history is special-category data under GDPR Art. 9. "
            "It is retained for 10 years under pharmacy record-keeping duties; erasure "
            "requests are honoured for marketing and analytics stores only."
        ),
    },
    {
        "id": "POL-INS-002",
        "title": "Statutory insurance reimbursement",
        "source": "SGB V §129, Redcare Reimbursement Guide v2",
        "body": (
            "For statutorily insured customers the fixed co-payment applies and Redcare "
            "bills the fund directly. Private insurance customers pay upfront and "
            "receive an invoice suitable for reimbursement."
        ),
    },
    {
        "id": "POL-CAN-005",
        "title": "Order cancellation window",
        "source": "Redcare Terms of Sale v9 §6",
        "body": (
            "Orders can be cancelled free of charge until the picking process starts, "
            "typically within 45 minutes of placement. After dispatch the returns "
            "policy applies instead."
        ),
    },
]


# --- handlers -----------------------------------------------------------------------
def lookup_order(order_id: str) -> dict:
    key = order_id.upper().replace(" ", "").replace("-", "")
    record = _ORDERS.get(key)
    if record is None:
        return {
            "error": "not_found",
            "order_id": key,
            "detail": "No order with that number on this account.",
        }
    eta = (
        "delivered"
        if record["days"] is None or record["days"] < 0
        else str(date.today() + timedelta(days=record["days"]))
    )
    return {
        "order_id": key,
        "status": record["status"],
        "carrier": record["carrier"],
        "eta": eta if record["status"] != "awaiting_prescription" else "blocked",
        "items": record["items"],
        "value_eur": record["value_eur"],
        "prescription_required": record["prescription"],
        "source_system": "SAP-OMS",
    }


def check_stock(product: str) -> dict:
    key = product.strip().lower()
    match = next((k for k in _STOCK if k in key or key in k), None)
    if match is None:
        return {
            "error": "unknown_product",
            "product": product,
            "detail": "Not in the catalogue under that name.",
        }
    units, availability, ships = _STOCK[match]
    return {
        "product": match,
        "availability": availability,
        "units_available": units,
        "ships_in": ships,
        "source_system": "WMS-Sevenum",
    }


def check_interactions(medications: list[str]) -> dict:
    names = sorted({m.strip().lower() for m in medications if m and m.strip()})
    if len(names) < 2:
        return {
            "error": "insufficient_input",
            "detail": "At least two medications are needed for an interaction check.",
        }
    findings, worst = [], "NO_KNOWN_RISK"
    order = {"NO_KNOWN_RISK": 0, "LOW_RISK": 1, "MODERATE_RISK": 2, "HIGH_RISK": 3}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            sev, note = _INTERACTIONS.get(
                frozenset({a, b}), ("NO_KNOWN_RISK", "No documented interaction.")
            )
            findings.append({"pair": [a, b], "severity": sev, "note": note})
            if order[sev] > order[worst]:
                worst = sev
    return {
        "severity": worst,
        "summary": next(
            (f["note"] for f in findings if f["severity"] == worst), "No documented interaction."
        ),
        "findings": findings,
        "dataset": "ABDA-DB snapshot 2026-07-01",
        "disclaimer": "Screening only. A pharmacist must confirm before any change in therapy.",
        "source_system": "ABDA-DACON",
    }


def search_policy(query: str, top_k: int = 3) -> dict:
    """Deterministic keyword retrieval standing in for Azure AI Search hybrid retrieval."""
    q = {w for w in query.lower().replace("?", " ").split() if len(w) > 3}
    scored = []
    for doc in _POLICIES:
        hay = f"{doc['title']} {doc['body']}".lower()
        score = sum(1 for w in q if w in hay)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda p: -p[0])
    results = [
        {
            "id": d["id"],
            "title": d["title"],
            "source": d["source"],
            "snippet": d["body"],
            "score": round(s / max(len(q), 1), 3),
        }
        for s, d in scored[:top_k]
    ]
    return {
        "query": query,
        "results": results,
        "retrieved": len(results),
        "index": "policies-v12",
        "source_system": "AzureAISearch",
    }


def escalate_to_pharmacist(reason: str, summary: str, priority: str = "normal") -> dict:
    """Side-effecting: opens a real ticket. Gated behind human-in-the-loop approval."""
    ticket = "PHARM-" + hashlib.sha256(f"{reason}{summary}".encode()).hexdigest()[:6].upper()
    sla = {"urgent": "15 minutes", "normal": "2 hours", "low": "1 business day"}
    return {
        "ticket_id": ticket,
        "queue": "pharmacist-review",
        "priority": priority,
        "sla": sla.get(priority, "2 hours"),
        "reason": reason,
        "handover_summary": summary,
        "source_system": "ServiceNow",
    }


# --- registration -------------------------------------------------------------------
registry.register(
    ToolSpec(
        name="lookup_order",
        description=(
            "Look up the status, carrier, ETA and contents of a Redcare order by its order number."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order number, e.g. RC10045821"}
            },
            "required": ["order_id"],
        },
        handler=lookup_order,
        data_classification="confidential-health",
        systems_touched=("SAP-OMS",),
        owner="team-order-management",
        slo_p95_ms=400,
        scopes=("orders:read",),
    )
)

registry.register(
    ToolSpec(
        name="check_stock",
        description="Check availability, unit count and shipping window for a product.",
        parameters={
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product or active ingredient name"}
            },
            "required": ["product"],
        },
        handler=check_stock,
        data_classification="internal",
        systems_touched=("WMS-Sevenum",),
        owner="team-supply-chain",
        slo_p95_ms=250,
        scopes=("catalogue:read",),
    )
)

registry.register(
    ToolSpec(
        name="check_interactions",
        description=(
            "Screen two or more medications for known interactions. Returns a severity "
            "band and per-pair findings. Screening only — never a therapy decision."
        ),
        parameters={
            "type": "object",
            "properties": {
                "medications": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "description": "Active ingredient names",
                }
            },
            "required": ["medications"],
        },
        handler=check_interactions,
        data_classification="confidential-health",
        systems_touched=("ABDA-DACON",),
        owner="team-clinical-data",
        slo_p95_ms=600,
        scopes=("clinical:screen",),
    )
)

registry.register(
    ToolSpec(
        name="search_policy",
        description=(
            "Retrieve grounded passages from Redcare policy and regulatory documents "
            "(returns, prescriptions, GDPR, reimbursement, cancellation)."
        ),
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 3}},
            "required": ["query"],
        },
        handler=search_policy,
        data_classification="internal",
        systems_touched=("AzureAISearch",),
        owner="team-knowledge",
        slo_p95_ms=350,
        scopes=("knowledge:read",),
    )
)

registry.register(
    ToolSpec(
        name="escalate_to_pharmacist",
        description=(
            "Hand the conversation to a registered pharmacist. Use for anything "
            "involving dosage, contraindications, symptoms or a HIGH_RISK screen."
        ),
        parameters={
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "summary": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "urgent"]},
            },
            "required": ["reason", "summary"],
        },
        handler=escalate_to_pharmacist,
        side_effect=True,
        requires_approval=True,
        data_classification="confidential-health",
        systems_touched=("ServiceNow",),
        owner="team-customer-care",
        slo_p95_ms=900,
        scopes=("escalation:write",),
    )
)
