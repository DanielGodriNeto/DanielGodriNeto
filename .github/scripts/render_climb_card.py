"""Renders climb-card.svg: a fastfetch-style profile card with a climber on K2's east face.

1 GitHub contribution = 1 metre; the summit is K2 (8,611 m). Pure stdlib.
The scene is original artwork; the marked camps use approximate Abruzzi-side altitudes.
Usage:
  python render_climb_card.py OUT.svg                      # live data, needs GITHUB_TOKEN
  python render_climb_card.py OUT.svg --contributions 1101 --repos 37   # offline preview
"""
import argparse
import datetime as dt
import json
import os
import urllib.request
from html import escape

USER = "DanielGodriNeto"
SUMMIT_M = 8611
INK, SNOW, ICE, ROCK, AMBER = "#0f1419", "#e8eef2", "#7fb6d4", "#2b3640", "#e0a458"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

# (altitude m, x, y): the climbing line up the east face, from the glacier to the summit.
ROUTE = [
    (0, 262, 268), (5000, 258, 240), (6050, 248, 206), (6700, 238, 172),
    (7400, 226, 138), (7700, 218, 112), (8200, 206, 82), (8611, 198, 50),
]
LABELS = {5000: "BC 5,000", 8200: "Bottleneck", 8611: "8,611"}


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


def stars():
    out = []
    for i in range(22):
        x = (i * 97 + 13) % 330 + 5
        y = (i * 53 + 7) % 110 + 6
        r = 0.6 + (i % 3) * 0.3
        out.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{SNOW}" opacity="{0.25 + (i % 4) * 0.12:.2f}"/>')
    return "".join(out)


def drift():
    out = []
    for i in range(9):
        x = (i * 71 + 40) % 300 + 20
        dur = 6 + (i * 5) % 5
        delay = -((i * 2) % dur)
        out.append(
            f'<circle class="drift" cx="{x}" cy="20" r="1.1" '
            f'style="animation-duration:{dur}s;animation-delay:{delay}s"/>'
        )
    return "".join(out)


def climber(altitude):
    x, y = point_at(altitude)
    u = 2
    px = [  # (x, y, w, h, fill) on a 5x8 grid
        (1, 0, 3, 2, AMBER), (1, 2, 3, 3, SNOW), (0, 2, 1, 3, ICE),
        (1, 5, 1, 3, SNOW), (3, 5, 1, 3, SNOW), (4, 1, 1, 5, ICE),
    ]
    rects = "".join(
        f'<rect x="{a*u}" y="{b*u}" width="{w*u}" height="{h*u}" fill="{c}"/>' for a, b, w, h, c in px
    )
    return f'<g transform="translate({x - 5:.1f} {y - 16:.1f})"><g class="bob">{rects}</g></g>'


def route_markers():
    out = []
    for alt, label in LABELS.items():
        x, y = next((px, py) for a, px, py in ROUTE if a == alt)
        out.append(f'<circle cx="{x}" cy="{y}" r="2" fill="{AMBER}"/>')
        out.append(f'<text class="tag" x="{x + 7}" y="{y + 3}">{escape(label)}</text>')
    return "".join(out)


def scene(altitude):
    path = " ".join(f"{x},{y}" for _, x, y in ROUTE)
    return f'''<defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0a1016"/><stop offset="1" stop-color="#1b2a37"/>
    </linearGradient>
    <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(32)">
      <line x1="0" y1="0" x2="0" y2="5" stroke="#05080b" stroke-width="1.4"/>
    </pattern>
    <clipPath id="frame"><rect x="14" y="14" width="324" height="272" rx="4"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect x="14" y="14" width="324" height="272" fill="url(#sky)"/>
    {stars()}
    <polygon points="14,226 60,196 96,214 134,176 170,206 210,170 250,200 290,168 338,196 338,286 14,286" fill="#121b23"/>
    <polygon points="196,50 178,86 170,104 140,150 112,196 60,268 14,286 338,286 322,268 274,210 250,160 236,128 214,88" fill="#2f3d49"/>
    <polygon points="196,50 214,88 236,128 250,160 274,210 322,268 338,286 196,286 214,200 206,140 204,98" fill="#18212a"/>
    <polygon points="196,50 214,88 236,128 250,160 274,210 322,268 338,286 196,286 214,200 206,140 204,98" fill="url(#hatch)" opacity=".7"/>
    <polygon points="196,50 178,86 186,82 196,96 206,84 214,88" fill="#d6e2ea"/>
    <polygon points="196,50 214,88 206,84 204,98 198,70" fill="#7d94a4"/>
    <polygon points="140,150 150,164 132,176 118,190 112,196" fill="#c9d6df" opacity=".35"/>
    <path d="M14,262 Q110,246 190,258 T338,252 L338,286 L14,286 Z" fill="#1f2d39"/>
    <path d="M14,262 Q110,246 190,258 T338,252" fill="none" stroke="#4a6071" stroke-width="1"/>
    <polygon points="250,244 255,236 260,244" fill="{ICE}" opacity=".85"/>
    <polygon points="262,245 266,239 270,245" fill="{ICE}" opacity=".6"/>
    <polyline points="{path}" fill="none" stroke="{AMBER}" stroke-width="1.2" stroke-dasharray="3 4" opacity=".75"/>
    {route_markers()}
    <line x1="198" y1="50" x2="198" y2="32" stroke="{SNOW}" stroke-width="1.4"/>
    <polygon class="flag" points="198,32 214,36 198,41" fill="{AMBER}"/>
    {climber(altitude)}
    {drift()}
  </g>
  <rect x="14.5" y="14.5" width="323" height="271" rx="4" fill="none" stroke="{ROCK}"/>
  <text class="tag" x="22" y="278" style="fill:#7d8a96">K2 · East Face</text>'''


def render(contributions, repos, joined):
    meters = min(contributions, SUMMIT_M)
    frac = meters / SUMMIT_M
    bar_w = 300
    rows = [
        ("Name", "Daniel Godri Neto"),
        ("Study", "Computer Science, PUC-PR"),
        ("Focus", "Applied AI, game and graphics tooling"),
        ("Stack", "Python, Java, JavaScript"),
        ("Languages", "Portuguese, English (C1), Japanese (learning)"),
        ("Repos", f"{repos} public"),
        ("Joined", joined),
    ]
    lines = []
    y = 98
    for key, val in rows:
        lines.append(
            f'<text x="372" y="{y}"><tspan class="k">{escape(key)}</tspan>'
            f'<tspan class="v" x="466">{escape(val)}</tspan></text>'
        )
        y += 19
    alt = f"{meters:,} m of {SUMMIT_M:,} m"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="300" viewBox="0 0 820 300" role="img" aria-label="Profile card: a climber at {meters} metres on K2's east face, one contribution per metre">
  <style>
    text {{ font-family: {MONO}; font-size: 13px; fill: {SNOW}; }}
    .k {{ fill: {ICE}; font-weight: 700; }}
    .dim {{ fill: #7d8a96; font-size: 11px; }}
    .tag {{ font-size: 9px; fill: {AMBER}; }}
    .drift {{ fill: {SNOW}; opacity: .55; animation: fall linear infinite; }}
    .bob {{ animation: bob 2.4s ease-in-out infinite; }}
    .flag {{ transform-box: fill-box; transform-origin: left center; animation: wave 3s ease-in-out infinite; }}
    @keyframes fall {{ to {{ transform: translate(-30px, 250px); }} }}
    @keyframes bob {{ 50% {{ transform: translateY(-1.5px); }} }}
    @keyframes wave {{ 50% {{ transform: scaleX(.8); }} }}
    @media (prefers-reduced-motion: reduce) {{ .drift, .bob, .flag {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="819" height="299" rx="8" fill="{INK}" stroke="{ROCK}"/>
  <line x1="352" y1="24" x2="352" y2="276" stroke="{ROCK}"/>
  {scene(meters)}

  <text x="372" y="62" style="font-size:15px;font-weight:700">daniel<tspan style="fill:{ICE}">@</tspan>github</text>
  <line x1="372" y1="72" x2="468" y2="72" stroke="{ROCK}"/>
  {chr(10).join("  " + l for l in lines)}

  <text x="372" y="{y + 12}"><tspan class="k">Altitude</tspan><tspan class="v" x="466">{alt}</tspan></text>
  <rect x="372" y="{y + 24}" width="{bar_w}" height="6" rx="3" fill="{ROCK}"/>
  <rect x="372" y="{y + 24}" width="{max(bar_w * frac, 4):.1f}" height="6" rx="3" fill="{AMBER}"/>
  <text class="dim" x="372" y="{y + 48}">1 contribution = 1 metre. Summit: K2.</text>
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
