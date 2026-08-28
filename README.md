# CrewHub Security Triage Agent

A **LangGraph agent** (`langgraph` StateGraph: `load_declaration -> prove_agency -> emit_manifest`)
declared to [siem-soar](https://github.com/iestarks/siem-soar)'s
[Discover Agents pipeline](https://github.com/iestarks/siem-soar/actions/workflows/discover-agents.yml).

## Prove it is an agent (not just an agent account)

The graph's `prove_agency` node **runs the agency function** at build time:

```
digest = sha256("{app_id}|siem-soar:agency:v1|{framework}")   # recorded as "sha256:<hex>"
```

and emits `manifest.json` — the declaration siem-soar fetches, verifies, and
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

## Entra identity

| Field | Value |
|---|---|
| App (client) ID | `3e694bb8-50af-4ecc-808f-71d2adf0a3d7` |
| SP object ID | `0d99b53f-65c4-4fd1-93f0-e9032271eca7` |
| Tenant | `starksenterprise` |
| Framework | LangGraph |

The identity is a real app registration + service principal in Entra ID, so a
connected siem-soar sweep observes it and marks this agent **tenant-verified**.
