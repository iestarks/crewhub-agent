#!/usr/bin/env python3
"""Run the CrewHub LangGraph agent and emit manifest.json + proof certificate.

This is the executable proof of agency: the graph runs, the prove_agency node
executes, and the manifest — including the agency digest — is written by the
agent itself. Alongside the manifest it renders ``agency-proof.svg``, a
deterministic visual execution certificate (graph nodes + the exact function
call + digest + verification seal). Both artifacts are pure functions of the
declaration, so CI asserts ``git diff --exit-code`` on each as tamper
evidence.

Usage:
    python -m crewhub_agent.prove [manifest.json]
"""
from __future__ import annotations

import json
import os
import sys

from .agency import verify_proof
from .certificate import save_certificate
from .graph import run


def main(argv: list[str] | None = None) -> int:
    out = (argv or sys.argv[1:] or ["manifest.json"])[0]
    state = run()
    manifest = state["manifest"]
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
        fh.write("\n")
    proof = manifest["agency_proof"]
    ok = verify_proof(manifest)
    out_dir = os.path.dirname(os.path.abspath(out))
    svg = save_certificate(manifest, os.path.join(out_dir, "agency-proof.svg"),
                           verified=ok)
    print(f"agent      : {manifest['display_name']} "
          f"(framework={manifest['framework']})")
    print(f"app_id     : {manifest['app_id']}")
    print("nodes run  :")
    for t in proof["trail"]:
        print(f"  ✓ {t['node']:<18} {t['detail']}")
    print(f"digest     : {proof['digest']}")
    print(f"self-verify: {'PASS' if ok else 'FAIL'}")
    print(f"certificate: {svg}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

