"""Draw a stats card (SVG) for a GitHub organization's public repos.

Usage: python3 org_stats.py <org> <output.svg>
Needs GITHUB_TOKEN in the environment.
"""
import base64
import json
import os
import sys
import textwrap
import urllib.request
from xml.sax.saxutils import escape

API = "https://api.github.com"
LANG_COLORS = {
    "Kotlin": "#A97BFF", "Java": "#b07219", "Python": "#3572A5", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#563d7c", "C++": "#f34b7d",
    "C": "#555555", "Go": "#00ADD8", "Rust": "#dea584", "Dart": "#00B4AB", "Swift": "#F05138",
    "Shell": "#89e051",
}

# GitHub octicons (16px)
ICON_STAR = "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"
ICON_FORK = "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"
ICON_DOWNLOAD = "M2.75 14A1.75 1.75 0 0 1 1 12.25v-2.5a.75.75 0 0 1 1.5 0v2.5c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25v-2.5a.75.75 0 0 1 1.5 0v2.5A1.75 1.75 0 0 1 13.25 14ZM7.25 7.689V2a.75.75 0 0 1 1.5 0v5.689l1.97-1.969a.749.749 0 1 1 1.06 1.06l-3.25 3.25a.749.749 0 0 1-1.06 0L4.22 6.78a.749.749 0 1 1 1.06-1.06l1.97 1.969Z"
ICON_REPO = "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"

BG, BORDER, TITLE, TEXT, ACCENT, LINK = "#151515", "#e4e2e2", "#ffffff", "#9f9f9f", "#79ff97", "#58a6ff"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"
WIDTH = 495


def get(url, raw=False):
    headers = {"User-Agent": "org-stats-card"}
    if url.startswith(API):  # only send the token to the GitHub API
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
        headers["Accept"] = "application/vnd.github+json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return data if raw else json.loads(data)


def get_all(url):
    items, page = [], 1
    while True:
        batch = get(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}")
        items += batch
        if len(batch) < 100:
            return items
        page += 1


def fmt(n):
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def icon(path, x, y, color=ACCENT, size=16):
    scale = size / 16
    return f'<path transform="translate({x} {y}) scale({scale})" fill="{color}" d="{path}"/>'


def main(org, out):
    info = get(f"{API}/orgs/{org}")
    repos = [r for r in get_all(f"{API}/orgs/{org}/repos?type=public") if not r["fork"] and not r["archived"]]
    for r in repos:
        releases = get_all(f"{API}/repos/{org}/{r['name']}/releases")
        r["downloads"] = sum(a["download_count"] for rel in releases for a in rel["assets"])
    repos.sort(key=lambda r: (r["stargazers_count"], r["downloads"]), reverse=True)

    avatar = base64.b64encode(get(info["avatar_url"] + "&s=64", raw=True)).decode()
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)
    downloads = sum(r["downloads"] for r in repos)

    parts = []
    # Header
    parts.append(f'<clipPath id="av"><circle cx="39" cy="34" r="16"/></clipPath>')
    parts.append(f'<image href="data:image/png;base64,{avatar}" x="23" y="18" width="32" height="32" clip-path="url(#av)"/>')
    parts.append(f'<text x="66" y="32" fill="{TITLE}" font-size="18" font-weight="700">{escape(info.get("name") or org)}</text>')
    parts.append(f'<text x="66" y="48" fill="{TEXT}" font-size="12">Organization · {len(repos)} public repos</text>')

    # Totals
    totals = [(ICON_STAR, stars, "Stars"), (ICON_FORK, forks, "Forks"), (ICON_DOWNLOAD, downloads, "Downloads")]
    col = (WIDTH - 50) / len(totals)
    for i, (path, value, label) in enumerate(totals):
        x = 25 + i * col
        parts.append(icon(path, x, 76, size=18))
        parts.append(f'<text x="{x + 26}" y="91" fill="{TITLE}" font-size="20" font-weight="700">{fmt(value)}</text>')
        parts.append(f'<text x="{x + 26}" y="107" fill="{TEXT}" font-size="11">{label}</text>')
    parts.append(f'<line x1="25" y1="124" x2="{WIDTH - 25}" y2="124" stroke="#2a2a2a"/>')

    # One row per repo
    y = 146
    for r in repos:
        parts.append(icon(ICON_REPO, 25, y - 12, color=TEXT, size=14))
        parts.append(f'<text x="45" y="{y}" fill="{LINK}" font-size="14" font-weight="600">{escape(r["name"])}</text>')
        lines = textwrap.wrap(r["description"] or "", 72)[:2]
        if len(textwrap.wrap(r["description"] or "", 72)) > 2:
            lines[1] = lines[1][:69].rstrip() + "…"
        for j, line in enumerate(lines):
            parts.append(f'<text x="45" y="{y + 18 + j * 15}" fill="{TEXT}" font-size="12">{escape(line)}</text>')
        my = y + 22 + len(lines) * 15
        x = 45
        if r["language"]:
            parts.append(f'<circle cx="{x + 5}" cy="{my - 4}" r="5" fill="{LANG_COLORS.get(r["language"], "#8b8b8b")}"/>')
            parts.append(f'<text x="{x + 15}" y="{my}" fill="{TEXT}" font-size="12">{escape(r["language"])}</text>')
            x += 30 + 7 * len(r["language"])
        for path, value in ((ICON_STAR, r["stargazers_count"]), (ICON_FORK, r["forks_count"]), (ICON_DOWNLOAD, r["downloads"])):
            parts.append(icon(path, x, my - 11, color=TEXT, size=13))
            parts.append(f'<text x="{x + 17}" y="{my}" fill="{TEXT}" font-size="12">{fmt(value)}</text>')
            x += 30 + 7 * len(fmt(value))
        y = my + 30

    height = y - 12
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'font-family="{FONT}" role="img" aria-label="{escape(org)} organization stats">'
        f'<rect x="0.5" y="0.5" rx="4.5" width="{WIDTH - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>'
        + "".join(parts) + "</svg>\n"
    )
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        f.write(svg)
    print(f"{org}: {len(repos)} repos, {stars} stars, {forks} forks, {downloads} downloads -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
