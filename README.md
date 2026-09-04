# CrewHub Security Triage Agent

A **LangGraph agent** (`langgraph` StateGraph: `load_declaration -> prove_agency -> emit_manifest`)
declared to [siem-soar](https://github.com/iestarks/siem-soar)'s
[Discover Agents pipeline](https://github.com/iestarks/siem-soar/actions/workflows/discover-agents.yml).

## Prove it is an agent (not just an agent account)

The graph's `prove_agency` node **runs the agency function** at build time:

```
digest = sha256("{app_id}|siem-soar:agency:v1|{framework}")   # recorded as "sha256:<hex>"
```

and emits `manifest.json` plus **`agency-proof.svg`** — a deterministic visual
"execution certificate" (the graph nodes that ran with ✓, the exact
`prove_agency(...)` call, the digest, and a VERIFIED seal). Rendered by the
agent itself; a pure function of the declaration, so CI tamper-checks it with
`git diff` like the manifest. siem-soar fetches the manifest, verifies the
proof, and
cross-checks against the actual Microsoft Entra tenant (appId match ->
`tenant_verified` / high confidence; no match -> `provisioning_unverified` /
low confidence).

## Usage

```bash
pip install -r requirements.txt          # langgraph
python -m crewhub_agent.prove            # run the agent -> regenerate manifest.json
python -m crewhub_agent.verify           # recompute + verify the recorded digest
python -m crewhub_agent.triage --findings identities-run.csv --dry-run   # triage CLI (CrewAI optional)
```

CI (`.github/workflows/prove-agent.yml`) runs the agent on every push, asserts
the regenerated manifest byte-matches the committed one (tamper evidence), and
verifies the agency proof.

The declaration's `launcher` block (also carried in `manifest.json`) makes
this agent launchable from the USEA Agent Launcher UI: its **Dry run** mode
runs the triage CLI above through USEA's `POST /v1/agents/launch` (live mode
is not offered — the triage CLI has no live variant). See the siem-soar
README ("Declared Agents") for the launcher contract and trust boundary.

## Entra identity

| Field | Value |
|---|---|
| App (client) ID | `3e694bb8-50af-4ecc-808f-71d2adf0a3d7` |
| SP object ID | `0d99b53f-65c4-4fd1-93f0-e9032271eca7` |
| Tenant | `starksenterprise` |
| Framework | LangGraph |

The identity is a real app registration + service principal in Entra ID, so a
connected siem-soar sweep observes it and marks this agent **tenant-verified**.
