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
CAMPS = ["BC", "C1", "C2", "C3", "C4", "Bottleneck", "Summit"]    # names for ROUTE[1:], in order
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


def xy(col, row):
    return PANEL_X + col * CELL_W, PANEL_Y + (row + 0.5) * CELL_H


def route_svg(altitude):
    """Dashed full route, solid amber up to the climber, numbered camps (filled once reached)."""
    full = " ".join("%.1f,%.1f" % xy(c, r) for _, c, r in ROUTE)
    done = [(a, c, r) for a, c, r in ROUTE if a <= altitude]
    col, row = point_at(altitude)
    climbed = " ".join("%.1f,%.1f" % xy(c, r) for _, c, r in done) + " %.1f,%.1f" % xy(col, row)
    out = [f'<polyline points="{full}" fill="none" stroke="{SNOW}" stroke-width="1.2" stroke-dasharray="2 4" opacity=".55"/>',
           f'<polyline points="{climbed}" fill="none" stroke="{AMBER}" stroke-width="1.8"/>']
    for n, (alt, c, r) in enumerate(ROUTE[1:], 1):
        x, y = xy(c, r)
        fill = AMBER if alt <= altitude else INK
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{fill}" stroke="{AMBER}" stroke-width="1.2"/>')
        out.append(f'<text class="num" x="{x + 9:.1f}" y="{y + 3:.1f}">{n}</text>')
    x, y = xy(col, row)
    out.append(f'<circle class="me" cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{SNOW}" stroke="{AMBER}" stroke-width="2"/>')
    return "".join(out)


def scene(altitude):
    with open(ART, "rb") as f:
        png = base64.b64encode(f.read()).decode()
    return f'''<clipPath id="frame"><rect x="{PANEL_X}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" rx="4"/></clipPath>
  <image href="data:image/png;base64,{png}" x="{PANEL_X}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" clip-path="url(#frame)"/>
  {route_svg(altitude)}
  <rect x="{PANEL_X + .5}" y="{PANEL_Y + .5}" width="{PANEL_W - 1}" height="{PANEL_H - 1}" rx="4" fill="none" stroke="{ROCK}"/>
  <text class="tag" x="{PANEL_X + 10}" y="{PANEL_Y + PANEL_H - 10}" style="fill:#7d8a96">K2 · East Face</text>'''


def box(y, h, title):
    return (f'<rect x="440" y="{y}" width="360" height="{h}" rx="3" fill="none" stroke="{ROCK}"/>'
            f'<rect x="452" y="{y - 7}" width="{len(title) * 8 + 12}" height="14" fill="{INK}"/>'
            f'<text class="k" x="458" y="{y + 4}">{escape(title)}</text>')


def row(y, key, val):
    return f'<text x="458" y="{y}"><tspan class="k">{escape(key)}</tspan><tspan class="v" x="570">{escape(val)}</tspan></text>'


def render(contributions, repos, joined):
    meters = min(contributions, SUMMIT_M)
    nxt = next(((a, n) for n, (a, _, _) in enumerate(ROUTE[1:]) if a > meters), None)
    goal = f"{CAMPS[nxt[1]]}, {nxt[0]:,} m ({nxt[0] - meters:,} to go)" if nxt else "Summit reached"
    bar_w = 324
    climb = [
        row(70, "Altitude", f"{meters:,} m of {SUMMIT_M:,} m"),
        f'<rect x="458" y="80" width="{bar_w}" height="6" rx="3" fill="{ROCK}"/>',
        f'<rect x="458" y="80" width="{max(bar_w * meters / SUMMIT_M, 4):.1f}" height="6" rx="3" fill="{AMBER}"/>',
        row(110, "Next camp", goal),
        row(130, "Contributions", f"{contributions:,} (1 = 1 m)"),
        row(150, "Repos", f"{repos} public"),
        row(170, "Since", joined),
    ]
    camps = []
    for n, (alt, _, _) in enumerate(ROUTE[1:]):
        y = 252 + n * 20
        mark = ("●", AMBER) if alt <= meters else ("○", "#5d7488")
        camps.append(f'<text x="458" y="{y}"><tspan fill="{mark[1]}">{mark[0]}</tspan>'
                     f'<tspan x="480" class="k">{n + 1}</tspan><tspan x="506">{escape(CAMPS[n])}</tspan>'
                     f'<tspan x="640" class="dim">{alt:,} m</tspan></text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="528" viewBox="0 0 820 528" role="img" aria-label="Profile card: ASCII K2 with a climber at {meters} metres on the east face, one contribution per metre">
  <style>
    text {{ font-family: {MONO}; font-size: 13px; fill: {SNOW}; }}
    .k {{ fill: {ICE}; font-weight: 700; }}
    .dim {{ fill: #7d8a96; font-size: 12px; }}
    .tag {{ font-size: 9px; fill: {AMBER}; }}
    .num {{ font-size: 10px; font-weight: 700; fill: {AMBER}; paint-order: stroke; stroke: {INK}; stroke-width: 3px; }}
    .me {{ animation: pulse 1.8s ease-in-out infinite; }}
    @keyframes pulse {{ 50% {{ opacity: .4; }} }}
    @media (prefers-reduced-motion: reduce) {{ .me {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="819" height="527" rx="8" fill="{INK}" stroke="{ROCK}"/>
  {scene(meters)}
  <g transform="translate(0 52)">
  {box(40, 150, "Climb")}
  {chr(10).join(climb)}
  {box(214, 168, "Camps")}
  {chr(10).join(camps)}
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
