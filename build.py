#!/usr/bin/env python3
"""
Site builder for the daily brief.

Usage:  python3 build.py

Reads every raw brief from  _briefs/YYYY-MM-DD.html
Writes:
    briefs/YYYY-MM-DD.html   each brief, with nav bar + noindex injected
    index.html               a copy of the most recent brief
    archive.html             a dated list of every brief

Idempotent: safe to run as many times as you like. To publish a new brief,
drop the raw HTML into _briefs/ as YYYY-MM-DD.html and run this script.
"""

import os
import re
import html
import shutil
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_briefs")
OUT = os.path.join(ROOT, "briefs")

NOINDEX = '<meta name="robots" content="noindex, nofollow">'

NAV_CSS = """
<style id="site-nav-style">
  #site-nav{font-family:ui-sans-serif,-apple-system,"Segoe UI",system-ui,sans-serif;
    font-size:.78rem;letter-spacing:.02em;padding:.7rem 1.5rem;
    border-bottom:1px solid rgba(128,128,128,.28);display:flex;gap:1.1rem;
    align-items:center;flex-wrap:wrap;opacity:.85}
  #site-nav a{text-decoration:none;border-bottom:none;color:inherit;opacity:.75}
  #site-nav a:hover{opacity:1;text-decoration:underline}
  #site-nav .sep{opacity:.35}
  #site-nav .now{font-weight:600;opacity:1}
</style>
"""


def nav_bar(current, prev_link, next_link):
    parts = ['<a href="{}index.html">Latest</a>'.format(current)]
    parts.append('<span class="sep">·</span>')
    parts.append('<a href="{}archive.html">All briefs</a>'.format(current))
    if prev_link:
        parts.append('<span class="sep">·</span>')
        parts.append('<a href="{}">← Previous</a>'.format(prev_link))
    if next_link:
        parts.append('<span class="sep">·</span>')
        parts.append('<a href="{}">Next →</a>'.format(next_link))
    return '<div id="site-nav">' + "".join(parts) + "</div>"


def inject(raw, nav):
    """Insert noindex into <head> and the nav bar just after <body>."""
    if NOINDEX not in raw:
        raw = re.sub(r"(<head[^>]*>)", r"\1\n" + NOINDEX, raw, count=1, flags=re.I)
    if "site-nav-style" not in raw:
        raw = re.sub(r"(</head>)", NAV_CSS + r"\1", raw, count=1, flags=re.I)
    raw = re.sub(r"(<body[^>]*>)", r"\1\n" + nav, raw, count=1, flags=re.I)
    return raw


def headline(raw, fallback):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S | re.I)
    if not m:
        return fallback
    text = re.sub(r"<[^>]+>", "", m.group(1))
    return " ".join(text.split()) or fallback


def pretty(d):
    try:
        y, m, dd = [int(x) for x in d.split("-")]
        return date(y, m, dd).strftime("%A %-d %B %Y")
    except Exception:
        return d


def main():
    os.makedirs(SRC, exist_ok=True)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    names = sorted(
        f[:-5] for f in os.listdir(SRC)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", f)
    )
    if not names:
        print("No briefs found in _briefs/. Nothing to build.")
        return

    entries = []
    for i, d in enumerate(names):
        raw = open(os.path.join(SRC, d + ".html"), encoding="utf-8").read()
        prev_link = names[i - 1] + ".html" if i > 0 else None
        next_link = names[i + 1] + ".html" if i < len(names) - 1 else None
        page = inject(raw, nav_bar("../", prev_link, next_link))
        open(os.path.join(OUT, d + ".html"), "w", encoding="utf-8").write(page)
        entries.append((d, headline(raw, "Daily brief")))

    # index.html = the most recent brief, at the root
    latest = names[-1]
    raw = open(os.path.join(SRC, latest + ".html"), encoding="utf-8").read()
    prev_link = "briefs/" + names[-2] + ".html" if len(names) > 1 else None
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(
        inject(raw, nav_bar("", prev_link, None))
    )

    rows = "\n".join(
        '<li><a href="briefs/{d}.html"><span class="d">{p}</span>'
        '<span class="t">{t}</span></a></li>'.format(
            d=d, p=html.escape(pretty(d)), t=html.escape(t)
        )
        for d, t in reversed(entries)
    )

    archive = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
""" + NOINDEX + """
<title>All briefs</title>
<style>
 :root{--ink:#1a1714;--soft:#6f6759;--paper:#faf7f2;--rule:#ded6c9;--accent:#8a3a1f}
 @media (prefers-color-scheme:dark){:root{--ink:#eae4da;--soft:#9a9184;--paper:#16140f;--rule:#3a352c;--accent:#d98a5f}}
 body{margin:0;background:var(--paper);color:var(--ink);
   font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;line-height:1.6}
 .wrap{max-width:44rem;margin:0 auto;padding:3.5rem 1.5rem 6rem}
 h1{font-size:2rem;margin:0 0 .3rem;font-weight:600;letter-spacing:-.01em}
 .sub{font-family:ui-sans-serif,-apple-system,system-ui,sans-serif;font-size:.8rem;
   color:var(--soft);margin-bottom:2.5rem}
 .sub a{color:var(--accent)}
 ul{list-style:none;padding:0;margin:0}
 li{border-top:1px solid var(--rule)}
 li:last-child{border-bottom:1px solid var(--rule)}
 li a{display:block;padding:1rem 0;text-decoration:none;color:inherit}
 li a:hover .t{color:var(--accent)}
 .d{display:block;font-family:ui-sans-serif,-apple-system,system-ui,sans-serif;
   font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--soft);margin-bottom:.2rem}
 .t{font-size:1.08rem;font-weight:600}
</style></head><body><div class="wrap">
<h1>All briefs</h1>
<div class="sub"><a href="index.html">← Back to the latest</a></div>
<ul>
""" + rows + """
</ul></div></body></html>
"""
    open(os.path.join(ROOT, "archive.html"), "w", encoding="utf-8").write(archive)
    print("Built {} brief(s). Latest: {}".format(len(names), latest))


if __name__ == "__main__":
    main()
