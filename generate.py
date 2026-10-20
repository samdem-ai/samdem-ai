"""Builds dark_mode.svg and light_mode.svg: ASCII padlock + neofetch-style info card.

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


def svg(theme, s):
    t = THEMES[theme]
    art = open(os.path.join(os.path.dirname(__file__) or ".", "ascii.txt")).read().split("\n")
    info = info_lines(t, s)
    line_h, font = 20, 16
    rows = max(len(art), len(info))
    height = rows * line_h + 40
    art_x, info_x = 20, 440
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',monospace" width="1020px" height="{height}px" font-size="{font}px">',
        f'<rect width="1020px" height="{height}px" fill="{t["bg"]}" rx="15"/>',
        f'<text x="{art_x}" y="30" fill="{t["text"]}" xml:space="preserve">',
    ]
    for i, row in enumerate(art):
        parts.append(f'<tspan x="{art_x}" y="{30 + i * line_h}">{html.escape(row)}</tspan>')
    parts.append("</text>")
    parts.append(f'<text x="{info_x}" y="30" fill="{t["text"]}" xml:space="preserve">')
    for i, row in enumerate(info):
        parts.append(f'<tspan x="{info_x}" y="{30 + i * line_h}">{row}</tspan>')
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
