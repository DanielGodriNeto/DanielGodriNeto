"""Renders climb-card.svg: a fastfetch-style profile card with an ASCII K2 with a progress marker on the east face.

1 GitHub contribution = 1 metre; the summit is K2 (8,611 m). Pure stdlib.
The scene is k2-ascii.png (ASCII art, made by make_k2_ascii.py); camps use approximate Abruzzi-side altitudes.
Usage:
  python render_climb_card.py OUT.svg                      # live data, needs GITHUB_TOKEN
  python render_climb_card.py OUT.svg --contributions 1101 --repos 37   # offline preview
"""
import argparse
import base64
import datetime as dt
import json
import os
import urllib.request
from html import escape

USER = "DanielGodriNeto"
SUMMIT_M = 8611
INK, SNOW, ICE, ROCK, AMBER = "#0f1419", "#e8eef2", "#7fb6d4", "#2b3640", "#e0a458"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

# (altitude m, col, row) on the east face of k2-ascii.png (260 x 195 characters), glacier to summit.
ROUTE = [
    (0, 176, 148), (5000, 186, 124), (6050, 196, 100), (6700, 188, 80),
    (7400, 168, 64), (7700, 148, 52), (8200, 124, 32), (8611, 98, 4),
]
LABELS = {5000: "BC 5,000", 8200: "Bottleneck", 8611: "8,611"}
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "k2-ascii.png")
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 14, 14, 400, 500
COLS, ROWS = 260, 195
CELL_W, CELL_H = PANEL_W / COLS, PANEL_H / ROWS


def api(url, token, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "climb-card")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_stats(token):
    user = api(f"https://api.github.com/users/{USER}", token)
    created = dt.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    parts = []
    for year in range(created.year, now.year + 1):
        end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        start = max(dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc), created)
        parts.append(
            f'y{year}: contributionsCollection(from: "{start:%Y-%m-%dT%H:%M:%SZ}", '
            f'to: "{end:%Y-%m-%dT%H:%M:%SZ}") {{ contributionCalendar {{ totalContributions }} }}'
        )
    query = f'{{ user(login: "{USER}") {{ {" ".join(parts)} }} }}'
    data = api("https://api.github.com/graphql", token, {"query": query})
    total = sum(v["contributionCalendar"]["totalContributions"] for v in data["data"]["user"].values())
    return total, user["public_repos"], created.strftime("%Y-%m")


def point_at(altitude):
    """Interpolate the route position for an altitude in metres."""
    for (a0, x0, y0), (a1, x1, y1) in zip(ROUTE, ROUTE[1:]):
        if altitude <= a1:
            t = (altitude - a0) / (a1 - a0)
            return x0 + t * (x1 - x0), y0 + t * (y1 - y0)
    return ROUTE[-1][1], ROUTE[-1][2]


def marker(col, row, char, cls):
    x = PANEL_X + col * CELL_W
    y = PANEL_Y + (row + 1) * CELL_H
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}">{char}</text>'


def scene(altitude):
    col, row = point_at(altitude)
    with open(ART, "rb") as f:
        png = base64.b64encode(f.read()).decode()
    tags = []
    for alt, label in LABELS.items():
        c, r = next((c, r) for a, c, r in ROUTE if a == alt)
        tags.append(marker(c, r, "o", "pin"))
        tags.append(f'<text class="tag" x="{PANEL_X + (c + 3) * CELL_W:.1f}" y="{PANEL_Y + (r + 1) * CELL_H:.1f}">{escape(label)}</text>')
    return f'''<clipPath id="frame"><rect x="{PANEL_X}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" rx="4"/></clipPath>
  <image href="data:image/png;base64,{png}" x="{PANEL_X}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" clip-path="url(#frame)"/>
  {"".join(tags)}
  {marker(col, row, "@", "me")}
  <rect x="{PANEL_X + .5}" y="{PANEL_Y + .5}" width="{PANEL_W - 1}" height="{PANEL_H - 1}" rx="4" fill="none" stroke="{ROCK}"/>
  <text class="tag" x="{PANEL_X + 10}" y="{PANEL_Y + PANEL_H - 10}" style="fill:#7d8a96">K2 · East Face</text>'''


def render(contributions, repos, joined):
    meters = min(contributions, SUMMIT_M)
    frac = meters / SUMMIT_M
    bar_w = 300
    rows = [
        ("Name", "Daniel Godri Neto"),
        ("Study", "Computer Science, PUC-PR"),
        ("Focus", "Applied AI, graphics, games"),
        ("Stack", "Python, Java, JavaScript"),
        ("Languages", "PT, EN (C1), JA (learning)"),
        ("Repos", f"{repos} public"),
        ("Joined", joined),
    ]
    lines = []
    y = 98
    for key, val in rows:
        lines.append(
            f'<text x="448" y="{y}"><tspan class="k">{escape(key)}</tspan>'
            f'<tspan class="v" x="542">{escape(val)}</tspan></text>'
        )
        y += 19
    alt = f"{meters:,} m of {SUMMIT_M:,} m"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="528" viewBox="0 0 820 528" role="img" aria-label="Profile card: a climber at {meters} metres on K2's east face, one contribution per metre">
  <style>
    text {{ font-family: {MONO}; font-size: 13px; fill: {SNOW}; }}
    .k {{ fill: {ICE}; font-weight: 700; }}
    .dim {{ fill: #7d8a96; font-size: 11px; }}
    .tag {{ font-size: 9px; fill: {AMBER}; }}
    .pin {{ fill: {AMBER}; font-size: 8px; font-weight: 700; }}
    .me {{ fill: {AMBER}; font-size: 12px; font-weight: 700; animation: pulse 1.8s ease-in-out infinite; }}
    @keyframes pulse {{ 50% {{ opacity: .35; }} }}
    @media (prefers-reduced-motion: reduce) {{ .me {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="819" height="527" rx="8" fill="{INK}" stroke="{ROCK}"/>
  <line x1="428" y1="24" x2="428" y2="504" stroke="{ROCK}"/>
  {scene(meters)}

  <g transform="translate(0 110)">
  <text x="448" y="62" style="font-size:15px;font-weight:700">daniel<tspan style="fill:{ICE}">@</tspan>github</text>
  <line x1="448" y1="72" x2="544" y2="72" stroke="{ROCK}"/>
  {chr(10).join("  " + l for l in lines)}

  <text x="448" y="{y + 12}"><tspan class="k">Altitude</tspan><tspan class="v" x="542">{alt}</tspan></text>
  <rect x="448" y="{y + 24}" width="{bar_w}" height="6" rx="3" fill="{ROCK}"/>
  <rect x="448" y="{y + 24}" width="{max(bar_w * frac, 4):.1f}" height="6" rx="3" fill="{AMBER}"/>
  <text class="dim" x="448" y="{y + 48}">1 contribution = 1 metre. Summit: K2.</text>
  </g>
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--contributions", type=int)
    ap.add_argument("--repos", type=int)
    args = ap.parse_args()
    if args.contributions is not None and args.repos is not None:
        stats = (args.contributions, args.repos, "2026-03")
    else:
        stats = fetch_stats(os.environ["GITHUB_TOKEN"])
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(*stats))


if __name__ == "__main__":
    main()
