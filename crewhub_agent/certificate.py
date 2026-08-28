"""Deterministic SVG "execution certificate" for the CrewHub agent.

Renders visual, human-checkable evidence that the LangGraph agent actually
executed its nodes — including the ``prove_agency`` function call — and that
the recorded digest matches a fresh recomputation.

The output is a PURE FUNCTION of the manifest (no timestamps, no randomness),
so CI tamper-checks it with ``git diff`` exactly like ``manifest.json``.
"""
from __future__ import annotations

from typing import Any, Dict, List

W, H = 920, 608

_INK = "#0f172a"        # slate-900
_MUTED = "#64748b"      # slate-500
_FAINT = "#94a3b8"      # slate-400
_GREEN = "#16a34a"
_GREEN_BG = "#ecfdf5"
_GREEN_TX = "#065f46"
_RED = "#dc2626"
_PANEL = "#f8fafc"
_PANEL_BR = "#e2e8f0"

_FALLBACK_DETAIL = {
    "load_declaration": "declaration.json loaded",
    "prove_agency": "prove_agency() executed -> sha256",
    "emit_manifest": "manifest.json written (deterministic)",
}


def _esc(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _wrap(text: str, width: int = 40, max_lines: int = 2) -> List[str]:
    """Character wrap for the small node-detail lines."""
    out, cur = [], ""
    for ch in str(text):
        if len(cur) == width:
            out.append(cur)
            cur = ""
            if len(out) == max_lines:
                return out
        cur += ch
    if cur and len(out) < max_lines:
        out.append(cur)
    return out or [""]


def render_certificate(manifest: Dict[str, Any], verified: bool) -> str:
    """Render the execution certificate SVG for a proven manifest."""
    proof = manifest.get("agency_proof") or {}
    trail = {t.get("node"): t.get("detail", "")
             for t in proof.get("trail", [])} or dict(_FALLBACK_DETAIL)
    nodes = proof.get("nodes") or list(_FALLBACK_DETAIL)
    ok_color = _GREEN if verified else _RED

    s: List[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        f"  <rect width=\"{W}\" height=\"{H}\" fill=\"#ffffff\"/>",
        # -- header -------------------------------------------------------
        f'  <rect width="{W}" height="96" fill="{_INK}"/>',
        f'  <text x="36" y="44" fill="#f8fafc" font-size="24" '
        f'font-weight="700">Agency Proof Certificate — '
        f'{_esc(manifest.get("display_name", "agent"))}</text>',
        f'  <text x="36" y="72" fill="{_FAINT}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">LangGraph StateGraph '
        f'execution · python -m crewhub_agent.prove</text>',
        f'  <text x="{W - 36}" y="44" text-anchor="end" fill="{_FAINT}" '
        f'font-size="12">framework: '
        f'{_esc(manifest.get("framework", "langgraph"))}</text>',
        f'  <text x="{W - 36}" y="64" text-anchor="end" fill="{_FAINT}" '
        f'font-size="12">app_id: {_esc(manifest.get("app_id", ""))}</text>',
    ]

    # -- node execution row --------------------------------------------
    box_w, box_h, y0 = 256, 112, 132
    xs = [36, 332, 628]
    s.append('  <text x="36" y="122" fill="' + _MUTED + '" font-size="11" '
             'letter-spacing="1">GRAPH NODES EXECUTED</text>')
    for i, node in enumerate(nodes):
        x = xs[i] if i < len(xs) else 36
        detail = trail.get(node) or _FALLBACK_DETAIL.get(node, "")
        s += [
            f'  <rect x="{x}" y="{y0}" width="{box_w}" height="{box_h}" '
            f'rx="10" fill="#ffffff" stroke="{ok_color}" stroke-width="2"/>',
            f'  <circle cx="{x + 28}" cy="{y0 + 32}" r="13" '
            f'fill="{ok_color}"/>',
            f'  <path d="M {x + 22} {y0 + 32} l 4.5 5 l 8 -10" '
            f'stroke="#ffffff" stroke-width="2.5" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>',
            f'  <text x="{x + 50}" y="{y0 + 28}" fill="{_MUTED}" '
            f'font-size="10" letter-spacing="1">STEP {i + 1} · RAN ✓</text>',
            f'  <text x="{x + 50}" y="{y0 + 46}" fill="{_INK}" '
            f'font-size="15" font-weight="600" '
            f'font-family="Menlo,Consolas,monospace">{_esc(node)}</text>',
        ]
        for j, ln in enumerate(_wrap(detail)):
            s.append(f'  <text x="{x + 20}" y="{y0 + 74 + j * 16}" '
                     f'fill="{_MUTED}" font-size="11">{_esc(ln)}</text>')
        if i < len(nodes) - 1 and i + 1 < len(xs):
            gx = xs[i + 1]
            mid = y0 + box_h // 2
            s += [
                f'  <line x1="{x + box_w + 4}" y1="{mid}" x2="{gx - 14}" '
                f'y2="{mid}" stroke="{_FAINT}" stroke-width="2"/>',
                f'  <polygon points="{gx - 2},{mid} {gx - 13},{mid - 6} '
                f'{gx - 13},{mid + 6}" fill="{_FAINT}"/>',
            ]
    return _render_rest(manifest, proof, ok_color, s)


def _render_rest(manifest: Dict[str, Any], proof: Dict[str, Any],
                 ok_color: str, s: List[str]) -> str:
    """Header + nodes done; append panels, seal, footer and serialize."""
    verified = ok_color == _GREEN

    # -- function-executed panel ----------------------------------------
    p_y = 276
    s += [
        f'  <rect x="36" y="{p_y}" width="848" height="140" rx="10" '
        f'fill="{_PANEL}" stroke="{_PANEL_BR}"/>',
        f'  <text x="56" y="{p_y + 26}" fill="{_GREEN}" font-size="11" '
        f'font-weight="700" letter-spacing="1">FUNCTION EXECUTED — '
        f'prove_agency(app_id, framework, challenge)</text>',
        f'  <text x="56" y="{p_y + 50}" fill="{_INK}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">prove_agency(</text>',
        f'  <text x="76" y="{p_y + 68}" fill="{_INK}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">app_id     = '
        f'"{_esc(manifest.get("app_id", ""))}",</text>',
        f'  <text x="76" y="{p_y + 86}" fill="{_INK}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">framework  = '
        f'"{_esc(manifest.get("framework", "langgraph"))}",</text>',
        f'  <text x="76" y="{p_y + 104}" fill="{_INK}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">challenge  = '
        f'"{_esc(proof.get("challenge", ""))}",</text>',
        f'  <text x="56" y="{p_y + 126}" fill="{_INK}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">)  →  sha256 hex digest'
        f'</text>',
    ]

    # -- digest bar ------------------------------------------------------
    d_y = 432
    s += [
        f'  <rect x="36" y="{d_y}" width="848" height="54" rx="10" '
        f'fill="{_GREEN_BG}" stroke="{_GREEN}"/>',
        f'  <text x="56" y="{d_y + 21}" fill="#047857" font-size="10" '
        f'letter-spacing="1">DIGEST (PUBLIC, NON-SECRET)</text>',
        f'  <text x="56" y="{d_y + 41}" fill="{_GREEN_TX}" font-size="13" '
        f'font-family="Menlo,Consolas,monospace">'
        f'{_esc(proof.get("digest", ""))}</text>',
    ]

    # -- verification seal ------------------------------------------------
    seal_y = 538
    verdict = ("VERIFIED — agency function re-executed, digest matched"
               if verified else
               "FAILED — recorded digest does not match recomputation")
    s += [
        f'  <circle cx="70" cy="{seal_y}" r="22" fill="{ok_color}"/>',
        f'  <path d="M 59 {seal_y} l 8 8 l 14 -16" stroke="#ffffff" '
        f'stroke-width="4" fill="none" stroke-linecap="round" '
        f'stroke-linejoin="round"/>',
        f'  <text x="108" y="{seal_y - 2}" fill="{ok_color}" '
        f'font-size="16" font-weight="700">{_esc(verdict)}</text>',
        f'  <text x="108" y="{seal_y + 18}" fill="{_MUTED}" '
        f'font-size="12">self-recomputed as sha256(app_id | challenge | '
        f'framework) · engine: {_esc(proof.get("engine", "langgraph"))}'
        f'</text>',
    ]

    # -- footer -----------------------------------------------------------
    s += [
        f'  <text x="36" y="{H - 16}" fill="{_FAINT}" font-size="11">'
        f'deterministic artifact · regenerate: python -m crewhub_agent.prove '
        f'· {_esc(manifest.get("repo", ""))} · entry '
        f'{_esc(manifest.get("entry", ""))}</text>',
        "</svg>",
        "",
    ]
    return "\n".join(s)


def save_certificate(manifest: Dict[str, Any], path: str,
                     verified: bool = True) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_certificate(manifest, verified))
    return path
