"""Renders climb-card.svg: a fastfetch-style profile card with a climber on K2.

1 GitHub contribution = 1 metre; the summit is K2 (8,611 m). Pure stdlib.
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

COLS, ROWS = 40, 19     # ASCII mountain grid
CW, RH = 8.0, 12.5      # cell width / row height in px
X0, Y0 = 14.0, 52.0     # top-left of the grid
SUMMIT_COL = 19


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


def snow_flakes():
    flakes = []
    for i in range(10):
        x = X0 + (i * 83 + 17) % 300
        dur = 7 + (i * 5) % 6
        delay = -((i * 3) % dur)
        ch = "*" if i % 3 == 0 else "."
        flakes.append(
            f'<text class="flake" x="{x:.0f}" y="30" '
            f'style="animation-duration:{dur}s;animation-delay:{delay}s">{ch}</text>'
        )
    return "\n    ".join(flakes)


def edges(i):
    left = max(SUMMIT_COL - round(i * 0.95), 0)
    right = min(SUMMIT_COL + 1 + round(i * 0.85) + (2 if i > 10 else 0), COLS - 1)
    return left, right


def fill_char(i):
    if i < 3:
        return " "
    if i < 8:
        return "."
    if i < 13:
        return ":"
    return "#"


def mountain_rows(climber_row, climber_col):
    out = []
    for i in range(ROWS):
        left, right = edges(i)
        body = [fill_char(i)] * (right - left - 1)
        if i == climber_row:
            body[climber_col - left - 1] = " "
        text = " " * left + "/" + "".join(body) + "\\"
        y = Y0 + i * RH
        out.append(
            f'<text xml:space="preserve" class="m" x="{X0}" y="{y:.1f}" '
            f'textLength="{len(text) * CW:.1f}" lengthAdjust="spacing">{escape(text)}</text>'
        )
    return "\n    ".join(out)


def climber(frac):
    row = min(max(round((1 - frac) * (ROWS - 1)), 0), ROWS - 1)
    left, _ = edges(row)
    col = left + 2
    x = X0 + col * CW
    y = Y0 + row * RH
    return row, col, f'<text class="bob" x="{x:.1f}" y="{y:.1f}" style="fill:{AMBER};font-weight:700">@</text>'


def render(contributions, repos, joined):
    meters = min(contributions, SUMMIT_M)
    frac = meters / SUMMIT_M
    c_row, c_col, c_glyph = climber(frac)
    pole_x = X0 + (SUMMIT_COL + 1) * CW
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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="300" viewBox="0 0 820 300" role="img" aria-label="Profile card: a climber at {meters} metres on K2, one contribution per metre">
  <style>
    text {{ font-family: {MONO}; font-size: 13px; fill: {SNOW}; }}
    .k {{ fill: {ICE}; font-weight: 700; }}
    .dim {{ fill: #7d8a96; font-size: 11px; }}
    .m {{ fill: #5b6b78; font-size: 12px; white-space: pre; }}
    .flake {{ fill: {SNOW}; opacity: .6; animation: fall linear infinite; }}
    .bob {{ animation: bob 2.4s ease-in-out infinite; }}
    .flag {{ transform-box: fill-box; transform-origin: left center; animation: wave 3s ease-in-out infinite; }}
    @keyframes fall {{ to {{ transform: translate(-26px, 240px); }} }}
    @keyframes bob {{ 50% {{ transform: translateY(-1.5px); }} }}
    @keyframes wave {{ 50% {{ transform: scaleX(.82); }} }}
    @media (prefers-reduced-motion: reduce) {{ .flake, .bob, .flag {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="819" height="299" rx="8" fill="{INK}" stroke="{ROCK}"/>
  <line x1="352" y1="24" x2="352" y2="276" stroke="{ROCK}"/>

  <g>
    {mountain_rows(c_row, c_col)}
    <text x="{pole_x:.1f}" y="{Y0 - RH:.1f}" text-anchor="middle" class="m">|</text>
    <text class="flag" x="{pole_x + 3:.1f}" y="{Y0 - RH - 2:.1f}" style="fill:{AMBER};font-weight:700">&gt;</text>
    {c_glyph}
    {snow_flakes()}
  </g>

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
