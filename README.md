# CrewHub Security Triage Agent

A self-contained [CrewAI](https://www.crewai.com/) + OpenAI agent that turns
`siem-soar`'s discover-agents findings into actionable security tickets.

This repo is the **owner** of the agent; `siem-soar` consumes it only through
its declarative `manifest.json` (see the *Repo-declared agents* section of
`siem-soar`'s README). The agent is therefore auditable and visible in siem-soar's
**agent discovery verification report** without siem-soar needing a Microsoft
Entra Agent ID for it.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # or AZURE_OPENAI_ENDPOINT + key
python3 crewhub_agent.py --repo iestarks/siem-soar --findings findings/sample.csv
python3 crewhub_agent.py --repo iestarks/siem-soar --dry-run   # no LLM call
```

## Manifest contract

`manifest.json` is read by `siem-soar/scripts/declared_agents.py`. Fields mirror
the row shape produced by `discover-agents.build_rows`, so a declared agent
appears in the report's **Agent inventory** and **Entra Agent ID entities**
sections with `is_agent = true`.
