#!/usr/bin/env python3
"""Verify a CrewHub manifest's agency proof — mirrors siem-soar's verifier.

    python -m crewhub_agent.verify [manifest.json]

Exit 0 = the recorded digest matches a fresh run of prove_agency (a
functioning agent produced this manifest); exit 1 = tampered/stale.
"""
from __future__ import annotations

import json
import sys

from .agency import verify_proof


def main(argv: list[str] | None = None) -> int:
    path = (argv or sys.argv[1:] or ["manifest.json"])[0]
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    ok = verify_proof(manifest)
    print(f"{'VERIFIED' if ok else 'FAILED'}: {path} "
          f"({manifest.get('display_name')} · {manifest.get('app_id')})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
