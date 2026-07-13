"""Renders cs2-stats.json (a delayed/anonymized aggregate snapshot, never real actionable
trade-up opportunities -- see the source project's src/profile_card_export.py) into a small
SVG card for the profile README. Pure stdlib, no dependencies -- matches this workflow's own
minimal-tooling convention."""
import json
import sys
from pathlib import Path

WIDTH = 480
HEIGHT = 150
BG = "#0a0c0a"
BORDER = "#262b26"
MUTED = "#6e786e"
TEXT = "#c9d1c9"
GREEN = "#39d97a"
RED = "#e0524f"


def _fmt_pct(v):
    if v is None:
        return "not yet verified", TEXT
    color = GREEN if v >= 0 else RED
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1f}%", color


def _fmt_int(v):
    return f"{v:,}" if isinstance(v, (int, float)) else "-"


def render(data: dict) -> str:
    avg_roi_text, avg_roi_color = _fmt_pct(data.get("population_avg_roi_pct_7d"))
    best_text, best_color = _fmt_pct(data.get("best_find_verified_roi_pct"))
    scanned = _fmt_int(data.get("total_candidates_scanned"))
    outcomes = _fmt_int(data.get("real_outcomes_logged"))
    agents = data.get("active_agents", "-")

    def stat(x, y, label, value, color):
        return (
            f'<text x="{x}" y="{y}" fill="{MUTED}" font-size="10" '
            f'letter-spacing="0.5" font-family="monospace">{label}</text>'
            f'<text x="{x}" y="{y + 22}" fill="{color}" font-size="20" font-weight="700" '
            f'font-family="monospace">{value}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="CS2 trade-up scanner stats">
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="4" fill="{BG}" stroke="{BORDER}"/>
  <text x="20" y="26" fill="{GREEN}" font-size="13" font-weight="700" letter-spacing="1" font-family="monospace">CS2 TRADE-UP SCANNER</text>
  <text x="{WIDTH - 20}" y="26" fill="{MUTED}" font-size="11" text-anchor="end" font-family="monospace">{agents}-agent population</text>
  <line x1="20" y1="36" x2="{WIDTH - 20}" y2="36" stroke="{BORDER}"/>
  {stat(20, 74, "POPULATION AVG ROI (7D)", avg_roi_text, avg_roi_color)}
  {stat(260, 74, "BEST VERIFIED FIND", best_text, best_color)}
  {stat(20, 118, "CANDIDATES SCANNED", scanned, TEXT)}
  {stat(260, 118, "REAL OUTCOMES LOGGED", outcomes, TEXT)}
  <line x1="20" y1="132" x2="{WIDTH - 20}" y2="132" stroke="{BORDER}"/>
  <text x="20" y="{HEIGHT - 10}" fill="{MUTED}" font-size="9" font-family="monospace">aggregate only -- not investment advice, updated periodically</text>
</svg>'''


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cs2-stats.json")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("cs2-card.svg")
    data = json.loads(src.read_text(encoding="utf-8"))
    out.write_text(render(data), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
