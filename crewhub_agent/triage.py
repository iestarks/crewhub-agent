#!/usr/bin/env python3
"""CrewHub triage CLI (LangGraph-declared agent, optional CrewAI runtime).

Turns a siem-soar ``identities-*.csv`` inventory into prioritized triage
tickets. Runs offline in --dry-run mode (no LLM); with crewai installed and
OPENAI_API_KEY set, executes a real CrewAI crew.

    python -m crewhub_agent.triage --findings identities-run.csv --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional

try:
    from crewai import Agent, Crew, Task  # optional runtime
    _CREWAI_OK = True
except Exception:
    _CREWAI_OK = False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_findings(path: str) -> List[dict]:
    if not path or not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def triage(repo: str, findings_csv: str, model: str, dry_run: bool) -> dict:
    findings = _read_findings(findings_csv)
    env = {
        "agent": "CrewHub-AgentsTriage",
        "repo": repo,
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
                    "display_name": r.get("display_name", "unknown"),
                    "identity_type": r.get("identity_type", ""),
                    "finding_orphan": r.get("finding_orphan", "") == "True",
                    "finding_secret": r.get("finding_secret", "") == "True",
                }
                for r in findings[:25]
            ],
        }
        return env

    if not _CREWAI_OK:
        env["result"] = {"error": "crewai not installed; use --dry-run"}
        return env
    agent = Agent(
        role="siem-soar security triage agent",
        goal=("Convert Entra/Azure discover-agents findings into prioritized, "
              "owner-attributed security tickets with remediation hints."),
        backstory=("You are CrewHub, the automated triage agent that consumes "
                   "the siem-soar agent-discovery verification report."),
        verbose=False,
        allow_delegation=False,
    )
    task = Task(
        description=(
            "Given the siem-soar discover-agents inventory rows for repo "
            f"{repo}, produce a prioritized triage list of at most 25 "
            "tickets. Each ticket must carry: display_name, identity_type, "
            "is_agent, credential_type, finding_orphan, finding_secret, "
            "finding_dormant, finding_never_used, owner_upn, app_id. "
            "Return ONLY a JSON list, no prose."
        ),
        expected_output="A JSON list of ticket objects.",
        agent=agent,
    )
    try:
        env["result"] = {"raw": str(
            Crew(agents=[agent], tasks=[task], verbose=False).kickoff())}
    except Exception as exc:
        env["result"] = {"error": str(exc)}
    return env


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="CrewHub security-triage agent")
    ap.add_argument("--repo", default="iestarks/siem-soar")
    ap.add_argument("--findings", default="")
    ap.add_argument("--model", default=os.environ.get("CREWHUB_MODEL",
                                                      "openai:gpt-4o"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    if not args.dry_run and not _CREWAI_OK:
        print("ERROR: crewai is required for a real run. Install with "
              "`pip install crewai openai` (or use --dry-run).", file=sys.stderr)
        return 2

    text = json.dumps(
        triage(args.repo, args.findings, args.model, args.dry_run), indent=2)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
