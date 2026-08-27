#!/usr/bin/env python3
"""CrewHub Security Triage Agent (CrewAI + OpenAI).

Turns the discover-agents inventory (``identities-*.csv`` or a manifest row
set) into prioritized security triage tickets. Declares itself to ``siem-soar``
via this repo's ``manifest.json``; ``siem-soar/scripts/declared_agents.py``
normalizes that manifest into a discovery row so the agent shows up in
siem-soar's agent-discovery **verification report** with ``is_agent = true`` --
without needing to be a Microsoft Entra Agent ID identity.

Run::

    export OPENAI_API_KEY=sk-...
    python3 crewhub_agent.py --repo iestarks/siem-soar --findings findings/sample.csv
    python3 crewhub_agent.py --repo iestarks/siem-soar --dry-run   # no LLM call
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from crewai import Agent, Crew, Task  # crewai>=0.100
    _CREWAI_OK = True
except Exception:  # deps not installed
    _CREWAI_OK = False

try:
    from langchain_openai import ChatOpenAI  # legacy provider path
    _LC_OK = True
except Exception:
    _LC_OK = False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_findings(path: str):
    if not path or not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _llm(model: str, temp: float = 0.2):
    """Build an OpenAI-backed LLM handle (CrewAI LLM or langchain fallback)."""
    if _CREWAI_OK:
        try:
            from crewai import LLM  # crewai>=0.100
            return LLM(provider="openai", model=model.replace("openai:", "", 1),
                       temperature=temp)
        except Exception:
            pass
    if _LC_OK:
        return ChatOpenAI(model_name=model.replace("openai:", "", 1),
                          temperature=temp, api_key=os.environ.get("OPENAI_API_KEY"))
    raise RuntimeError("neither crewai nor langchain_openai is available")


def build_agent(model: str = "openai:gpt-4o"):
    """The CrewAI agent: a security-triage specialist for siem-soar findings."""
    if not _CREWAI_OK:
        # Lightweight stub so --dry-run works even without deps installed.
        class _Stub:
            role = "siem-soar security triage agent (stub)"
            goal = "Triage siem-soar findings."
            backstory = "Stub agent; install crewai to enable real execution."

            def kickdown(self, *a, **k):
                return {"triaged": 0, "note": "stub: crewai not installed"}
        return _Stub()

    llm = _llm(model)
    return Agent(
        role="siem-soar security triage agent",
        goal=("Convert Entra/Azure discover-agents findings into prioritized, "
              "owner-attributed security tickets with remediation hints."),
        backstory=("You are CrewHub, the automated triage agent that consumes "
                   "the siem-soar agent-discovery verification report. You never "
                   "invent identity data -- you triage only the rows siem-soar "
                   "itself found."),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def triage(repo: str, findings_csv: str, model: str, dry_run: bool) -> dict:
    """Run triage over a findings CSV and return a result envelope."""
    findings = _read_findings(findings_csv)
    env = {
        "agent": "CrewHub-AgentsTriage",
        "repo": repo or os.environ.get("GHREPO", "iestarks/siem-soar"),
        "model": model,
        "generated_at": _now(),
        "source_findings": findings_csv,
        "finding_rows": len(findings),
        "dry_run": dry_run,
        "crewai_available": _CREWAI_OK,
    }
    if dry_run:
        env["result"] = {
            "triaged": len(findings),
            "note": "dry-run: no LLM call made",
            "tickets": [
                {
                    "display_name": r.get("displayName", "unknown"),
                    "finding_orphan": r.get("finding_orphan", "") == "True",
                    "finding_secret": r.get("finding_secret", "") == "True",
                }
                for r in findings[:25]
            ],
        }
        return env
        agent = build_agent(model)
    task = Task(
        description=(
            "Given the siem-soar discover-agents inventory rows for repo "
            f"{env['repo']}, produce a prioritized triage list of at most 25 "
            "tickets. Each ticket must carry: display_name, identity_type, "
            "is_agent, credential_type, finding_orphan, finding_secret, "
            "finding_dormant, finding_never_used, owner_upn, app_id. "
            "Return ONLY a JSON list, no prose."
        ),
        expected_output="A JSON list of ticket objects.",
        agent=agent,
    )
    if _CREWAI_OK:
        try:
            env["result"] = {"raw": str(Crew(
                agents=[agent], tasks=[task], verbose=False).kickoff())}
        except Exception as exc:  # surface but never crash the discovery flow
            env["result"] = {"error": str(exc)}
    else:
        env["result"] = {"raw": str(task.expected_output)}
    return env


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="CrewHub security-triage agent")
    ap.add_argument("--repo", default=os.environ.get("GHREPO", "iestarks/siem-soar"))
    ap.add_argument("--findings", default="")
    ap.add_argument("--model", default=os.environ.get("CREWHUB_MODEL", "openai:gpt-4o"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    if not args.dry_run and not _CREWAI_OK:
        print("ERROR: crewai is required for a real run. Install with "
              "`pip install -r requirements.txt` (or use --dry-run).",
              file=sys.stderr)
        return 2

    text = json.dumps(
        triage(args.repo, args.findings, args.model, args.dry_run), indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
