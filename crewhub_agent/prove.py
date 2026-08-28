#!/usr/bin/env python3
"""Run the CrewHub LangGraph agent and emit manifest.json.

This is the executable proof of agency: the graph runs, the prove_agency node
executes, and the manifest — including the agency digest — is written by the
agent itself. Regeneration is deterministic (no timestamps), so CI can assert
``git diff --exit-code manifest.json`` as tamper evidence.

Usage:
    python -m crewhub_agent.prove [manifest.json]
"""
from __future__ import annotations

import json
import sys

from .agency import verify_proof
from .graph import run


def main(argv: list[str] | None = None) -> int:
    out = (argv or sys.argv[1:] or ["manifest.json"])[0]
    state = run()
    manifest = state["manifest"]
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
        fh.write("\n")
    proof = manifest["agency_proof"]
    print(f"agent      : {manifest['display_name']} "
          f"(framework={manifest['framework']})")
    print(f"app_id     : {manifest['app_id']}")
    print(f"nodes run  : {' -> '.join(proof['nodes'])}")
    print(f"digest     : {proof['digest']}")
    ok = verify_proof(manifest)
    print(f"self-verify: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
