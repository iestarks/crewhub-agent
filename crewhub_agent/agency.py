"""Proof-of-agency for the CrewHub agent (LangGraph).

Contract shared with siem-soar ``scripts/declared_agents.py``:

    digest = sha256(f"{app_id}|{challenge}|{framework}").hexdigest()

A real agent RUNS this function (as a LangGraph node) at build time and
records the digest in ``manifest.json`` under ``agency_proof.digest`` as
``sha256:<hex>`` — a public, non-secret value that only proves a function
ran; knowing it lets anyone *verify* the proof, never impersonate anyone.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

AGENCY_CHALLENGE = "siem-soar:agency:v1"


def prove_agency(app_id: str, framework: str,
                 challenge: str = AGENCY_CHALLENGE) -> str:
    """The agency proof: a function the agent actually executes."""
    return hashlib.sha256(
        f"{app_id}|{challenge}|{framework}".encode("utf-8")).hexdigest()


def verify_proof(manifest: Dict[str, Any]) -> bool:
    """Recompute the recorded digest; True iff the agent's proof is intact."""
    proof = manifest.get("agency_proof") or {}
    recorded = proof.get("digest") or ""
    expected = "sha256:" + prove_agency(
        manifest.get("app_id", ""),
        manifest.get("framework", ""),
        proof.get("challenge", AGENCY_CHALLENGE),
    )
    return recorded == expected


def load_declaration(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
