"""The CrewHub agent as a LangGraph StateGraph.

Three nodes: load_declaration -> prove_agency -> emit_manifest.
``prove_agency`` is the node that proves this is a functioning agent and not
merely an "agent account": it runs the agency function and records the digest
that siem-soar's pipeline later recomputes.
"""
from __future__ import annotations

import os
from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from .agency import AGENCY_CHALLENGE, load_declaration, prove_agency

DECLARATION_PATH = os.path.join(os.path.dirname(__file__), "declaration.json")
NODES = ["load_declaration", "prove_agency", "emit_manifest"]


class AgentState(TypedDict):
    declaration: Dict[str, Any]
    digest: str
    manifest: Dict[str, Any]
    trail: list  # per-node execution evidence (deterministic)


def load_declaration_node(state: AgentState) -> Dict[str, Any]:
    path = os.environ.get("CREWHUB_DECLARATION", DECLARATION_PATH)
    d = load_declaration(path)
    trail = list(state.get("trail", [])) + [{
        "node": "load_declaration",
        "detail": f"declaration.json -> {d.get('display_name', '')}",
    }]
    return {"declaration": d, "trail": trail}


def prove_agency_node(state: AgentState) -> Dict[str, Any]:
    d = state["declaration"]
    digest = prove_agency(d["app_id"], d.get("framework", "langgraph"),
                          AGENCY_CHALLENGE)
    trail = list(state.get("trail", [])) + [{
        "node": "prove_agency",
        "detail": "prove_agency() executed -> sha256",
    }]
    return {"digest": digest, "trail": trail}


def emit_manifest_node(state: AgentState) -> Dict[str, Any]:
    d = state["declaration"]
    manifest = {
        "name": d.get("name"),
        "display_name": d.get("display_name"),
        "repo": d.get("repo"),
        "home": d.get("home"),
        "entry": d.get("entry"),
        "framework": d.get("framework", "langgraph"),
        "llm": d.get("llm"),
        "identity_type": d.get("identity_type", "DeclaredAgent"),
        "entra_identity": d.get("entra_identity", False),
        "app_id": d.get("app_id"),
        "object_id": d.get("object_id"),
        "blueprint_id": d.get("blueprint_id", ""),
        "owners": d.get("owners", []),
        "sponsors": d.get("sponsors", []),
        "credential_type": d.get("credential_type", "federated"),
        "created_on": d.get("created_on"),
        "agent_identity": d.get("agent_identity", True),
        "app_roles": d.get("app_roles", []),
        "fic_subjects": d.get("fic_subjects", []),
        "delegated_grants": d.get("delegated_grants", []),
        "launcher": d.get("launcher"),
        "agency_proof": {
            "function": "prove_agency",
            "challenge": AGENCY_CHALLENGE,
            "digest": "sha256:" + state["digest"],
            "executed": True,
            "engine": "langgraph",
            "nodes": NODES,
            "trail": list(state.get("trail", [])) + [{
                "node": "emit_manifest",
                "detail": "manifest.json written (deterministic)",
            }],
        },
    }
    return {"manifest": manifest}


def build_graph():
    """Compile the agent graph: load -> prove -> emit."""
    g = StateGraph(AgentState)
    g.add_node("load_declaration", load_declaration_node)
    g.add_node("prove_agency", prove_agency_node)
    g.add_node("emit_manifest", emit_manifest_node)
    g.add_edge(START, "load_declaration")
    g.add_edge("load_declaration", "prove_agency")
    g.add_edge("prove_agency", "emit_manifest")
    g.add_edge("emit_manifest", END)
    return g.compile()


def run() -> Dict[str, Any]:
    """Invoke the agent and return its final state (manifest included)."""
    return build_graph().invoke({})
