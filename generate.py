"""Builds dark_mode.svg and light_mode.svg: the linPEAS mascot + a neofetch-style info card.

Run locally with `python generate.py`. The GitHub Action runs it daily to refresh the stats.
"""
import html
import json
import os
import urllib.request

USER = "samdem-ai"
WIDTH = 58  # characters in the info column

INFO = [
    ("header", "samy@algiers"),
    ("OS", "CachyOS, Windows lab VMs"),
    ("Role", "Cybersecurity engineer"),
    ("Education", "ESTIN, Engineer + Master's (2026)"),
    ("Focus", "Reverse engineering, DFIR, AI red teaming"),
    ("Now", "HTB CPTS, open to SOC / IR roles"),
    ("Shell", "fish"),
    ("blank", ""),
    ("Languages.Programming", "Python, C, C++, TypeScript, Bash"),
    ("Languages.Real", "Arabic, French, English"),
    ("blank", ""),
    ("Tools.RE", "Ghidra, IDA Pro, YARA, x86/x64"),
    ("Tools.DFIR", "Velociraptor, Elastic, Wireshark"),
    ("blank", ""),
    ("section", "Contact"),
    ("Email", "m_debaili@estin.dz"),
    ("LinkedIn", "samy-debaili"),
    ("blank", ""),
    ("section", "GitHub Stats"),
    ("stats", ""),
]

THEMES = {
    "dark": {"bg": "#161b22", "text": "#c9d1d9", "key": "#ffa657", "value": "#a5d6ff", "dots": "#616e7f"},
    "light": {"bg": "#f6f8fa", "text": "#24292f", "key": "#953800", "value": "#0a3069", "dots": "#c2cfde"},
}


def github(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def stats():
    try:
        user = github(f"/users/{USER}")
        repos = github(f"/users/{USER}/repos?per_page=100&type=owner")
        stars = sum(r["stargazers_count"] for r in repos if not r["fork"])
        return user["public_repos"], stars, user["followers"]
    except Exception as e:  # keep the last good card rather than failing the build
        print("stats unavailable:", e)
        return None


def tspan(text, color):
    return f'<tspan fill="{color}">{html.escape(text)}</tspan>'


def dotted(key, value, t):
    dots = "." * max(1, WIDTH - len(key) - len(value) - 4)
    return tspan(key, t["key"]) + tspan(": ", t["text"]) + tspan(dots, t["dots"]) + " " + tspan(value, t["value"])


def info_lines(t, s):
    out = []
    for key, value in INFO:
        if key == "header":
            out.append(tspan(value, t["key"]) + tspan(" " + "-" * (WIDTH - len(value) - 1), t["dots"]))
        elif key == "section":
            out.append(tspan(f"- {value} ", t["text"]) + tspan("-" * (WIDTH - len(value) - 3), t["dots"]))
        elif key == "blank":
            out.append("")
        elif key == "stats":
            if s:
                repos, stars, followers = s
                out.append(dotted("Repos", f"{repos}  |  Stars: {stars}  |  Followers: {followers}", t))
            else:
                out.append(tspan("GitHub stats: refreshed daily", t["dots"]))
        else:
            out.append(dotted(key, value, t))
    return out


def pixel_art(x0, y0, size):
    """The linPEAS banner (see NOTICE.md) as SVG rects, merging horizontal runs of one colour."""
    rows = json.load(open(os.path.join(os.path.dirname(__file__) or ".", "banner.json")))
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            color = row[x]
            run = 1
            while x + run < len(row) and row[x + run] == color:
                run += 1
            if color:
                out.append(f'<rect x="{x0 + x * size}" y="{y0 + y * size}" width="{run * size}" height="{size}" fill="#{color}"/>')
            x += run
    return out, len(rows[0]) * size, len(rows) * size


def svg(theme, s):
    t = THEMES[theme]
    info = info_lines(t, s)
    line_h, font, pad = 20, 16, 30
    info_h = len(info) * line_h
    height = info_h + 2 * pad
    size = 8
    _, art_w, art_h = pixel_art(0, 0, size)
    art_x, art_y = 40, pad + (info_h - art_h) // 2 - 6
    art, _, _ = pixel_art(art_x, art_y, size)
    info_x = art_x + art_w + 50
    width = info_x + 580
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',monospace" width="{width}px" height="{height}px" font-size="{font}px">',
        f'<rect width="{width}px" height="{height}px" fill="{t["bg"]}" rx="15"/>',
        '<g shape-rendering="crispEdges">', *art, "</g>",
        f'<text x="{info_x}" y="{pad + 14}" fill="{t["text"]}" xml:space="preserve">',
    ]
    for i, row in enumerate(info):
        parts.append(f'<tspan x="{info_x}" y="{pad + 14 + i * line_h}">{row}</tspan>')
    parts.append("</text></svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    s = stats()
    for theme in THEMES:
        path = f"{theme}_mode.svg"
        if s is None and os.path.exists(path):
            continue
        with open(path, "w") as f:
            f.write(svg(theme, s))
        print("wrote", path, s)
