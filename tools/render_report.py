#!/usr/bin/env python3
"""Render the browsable report.

    python3 tools/render_report.py

Reads two hand-maintained files and writes one page:

    docs/TEST_PLAN.md   the written plan
    TEST_CASES.csv      the cases and their execution status
    -> docs/index.html

Edit either and re-run. Nothing else is generated.
"""
from __future__ import annotations

import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "docs" / "TEST_PLAN.md"
CASES = ROOT / "TEST_CASES.csv"
OUT = ROOT / "docs" / "index.html"
CSS = Path(__file__).parent / "report.css"

STATUS_CLASS = {"pass": "pass", "passed": "pass", "fail": "fail", "failed": "fail",
                "blocked": "blocked", "not run": "notrun", "": "notrun"}
FLAG = re.compile(r"^(Failure signature|CRITICAL|Watch for OBS)")
STEP_NUM = re.compile(r"^\d+\.\s*")


def inline(s: str) -> str:
    s = html.escape(str(s))
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ------------------------------------------------------------------ markdown
def render_markdown(text: str) -> tuple[str, list[tuple[str, str]]]:
    """A deliberately small subset: headings, paragraphs, lists, tables, quotes, code."""
    out: list[str] = []
    toc: list[tuple[str, str]] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(html.escape(lines[i]))
                i += 1
            out.append('<pre class="cmd"><code>%s</code></pre>' % "\n".join(body))
            i += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            if level == 1:
                out.append(f"<h1>{inline(title)}</h1>")
            elif level == 2:
                sid = slug(title)
                toc.append((sid, title))
                out.append(f'<section class="sec" id="{sid}"><h2>{inline(title)}</h2>')
            else:
                out.append(f"<h3>{inline(title)}</h3>")
            i += 1
            continue

        if stripped.startswith(">"):
            body = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                body.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append('<aside class="callout">%s</aside>' % inline(" ".join(body)))
            continue

        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head = rows[0] if len(rows) > 1 and set("".join(rows[1])) <= set("-: ") else None
            body = rows[2:] if head else rows
            t = ['<div class="tw"><table>']
            if head and any(h for h in head):
                t.append("<thead><tr>%s</tr></thead>" % "".join(f"<th>{inline(h)}</th>" for h in head))
            t.append("<tbody>%s</tbody></table></div>" % "".join(
                "<tr>%s</tr>" % "".join(f"<td>{inline(c)}</td>" for c in r) for r in body))
            out.append("".join(t))
            continue

        if re.match(r"^[-*] ", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i].strip()):
                items.append(inline(lines[i].strip()[2:]))
                i += 1
            out.append("<ul>%s</ul>" % "".join(f"<li>{x}</li>" for x in items))
            continue

        if re.match(r"^\d+\. ", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].strip()):
                items.append(inline(re.sub(r"^\d+\. ", "", lines[i].strip())))
                i += 1
            out.append('<ol class="numlist">%s</ol>' % "".join(f"<li>{x}</li>" for x in items))
            continue

        if stripped == "<!-- CASES -->":
            out.append("@@CASES@@")
            i += 1
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#|\||>|```|[-*] |\d+\. |<!--)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    body = "\n".join(out)
    # close each section before the next opens
    body = body.replace('<section class="sec"', '</section><section class="sec"', )
    body = body.replace('</section><section class="sec"', '<section class="sec"', 1)
    return body + "</section>", toc


# ------------------------------------------------------------------ cases
def field(row: dict, *names: str) -> str:
    """Column names drift; take the first that is present and non-empty."""
    for n in names:
        if row.get(n, "").strip():
            return row[n].strip()
    return ""


SUITE_NOTE = re.compile(r"^- \*\*(.+?)\*\*\s+[—-]\s+(.*)$")


def suite_notes(markdown: str) -> dict[str, str]:
    """Lines under '### Suite notes' are rendered above the suite they name."""
    block = re.search(r"### Suite notes\n(.*?)(?=\n#{2,3} |\n<!--)", markdown, re.S)
    if not block:
        return {}
    found = {}
    for line in block.group(1).splitlines():
        m = SUITE_NOTE.match(line.strip())
        if m:
            found[m.group(1).strip()] = m.group(2).strip()
    return found


def render_cases(rows: list[dict], notes: dict[str, str] | None = None
                 ) -> tuple[str, list[tuple[str, str]], dict]:
    notes = notes or {}
    out = ['<div class="filters no-print">'
           '<input type="search" id="q" placeholder="Filter cases…" aria-label="Filter cases">'
           '<select id="fp"><option value="">All priorities</option>'
           '<option>P0</option><option>P1</option><option>P2</option><option>P3</option></select>'
           '<select id="fs"><option value="">All results</option><option>Pass</option>'
           '<option>Fail</option><option>Blocked</option><option>Not Run</option></select>'
           '<span id="fcount"></span></div><div id="cases">']
    subs: list[tuple[str, str]] = []
    tally: dict[str, int] = {}
    last = None
    for r in rows:
        suite = field(r, "Section", "Suite")
        status = field(r, "Status") or "Not Run"
        tally[status] = tally.get(status, 0) + 1
        if suite != last:
            last = suite
            n = sum(1 for x in rows if field(x, "Section", "Suite") == suite)
            subs.append((slug(suite), suite))
            out.append(f'<div class="suite" id="{slug(suite)}"><h3>{html.escape(suite)}</h3>'
                       f'<span>{n} cases</span></div>')
            if suite in notes:
                out.append(f'<aside class="snote">{inline(notes[suite])}</aside>')
        cls = STATUS_CLASS.get(status.lower(), "notrun")
        out.append(
            f'<article class="case {r["Priority"]}" id="{r["Test Case ID"]}" '
            f'data-pri="{r["Priority"]}" data-status="{html.escape(status)}">'
            f'<header class="ch"><a class="tc" href="#{r["Test Case ID"]}">{r["Test Case ID"]}</a>'
            f'<h4>{inline(r["Title"])}</h4>'
            f'<span class="pri {r["Priority"]}">{r["Priority"]}</span>'
            f'<span class="status {cls}">{html.escape(status)}</span></header><dl>')
        for label, keys in (("Objective", ("Objective / Risk Covered", "Objective")),
                            ("Preconditions", ("Preconditions",)),
                            ("Test data", ("Test Data",))):
            value = field(r, *keys)
            if value and value != "-":
                out.append(f"<dt>{label}</dt><dd>{inline(value)}</dd>")
        steps = [STEP_NUM.sub("", s).strip()
                 for s in field(r, "Steps", "Test Steps").split("\n") if s.strip()]
        out.append("<dt>Steps</dt><dd><ol class='steps'>%s</ol></dd>" % "".join(
            "<li>%s</li>" % inline(s) for s in steps))
        exp = [e.lstrip("- ").strip()
               for e in field(r, "Expected Result", "Expected Results").split("\n") if e.strip()]
        out.append("<dt>Expected</dt><dd><ul class='exp'>%s</ul></dd>" % "".join(
            '<li%s>%s</li>' % (' class="flag"' if FLAG.match(e) else "", inline(e))
            for e in exp))
        for label, keys in (("Actual", ("Actual Result",)), ("Defect", ("Bug ID", "Defect ID")),
                            ("Tested on", ("Tested On",)), ("Notes", ("Notes",))):
            value = field(r, *keys)
            if value and value != "-":
                out.append(f"<dt>{label}</dt><dd>{inline(value)}</dd>")
        out.append("</dl></article>")
    out.append("</div>")
    return "".join(out), subs, tally


JS = """
<script>
(function(){
 var q=document.getElementById('q'),fp=document.getElementById('fp'),fs=document.getElementById('fs'),
     cnt=document.getElementById('fcount'),wrap=document.getElementById('cases');
 if(!wrap)return;
 var cards=[].slice.call(wrap.querySelectorAll('.case'));
 var heads=[].slice.call(wrap.querySelectorAll('.suite'));
 cards.forEach(function(c){c._t=c.textContent.toLowerCase();});
 function apply(){
  var s=q.value.trim().toLowerCase(),p=fp.value,st=fs.value,n=0;
  cards.forEach(function(c){
   var ok=(!p||c.dataset.pri===p)&&(!st||c.dataset.status===st)&&(!s||c._t.indexOf(s)>-1);
   c.classList.toggle('hide',!ok); if(ok)n++;
  });
  heads.forEach(function(h){
   var vis=0,el=h.nextElementSibling;
   while(el&&!el.classList.contains('suite')){
    if(el.classList.contains('case')&&!el.classList.contains('hide'))vis++;
    el=el.nextElementSibling;}
   h.style.display=vis?'':'none';});
  cnt.textContent=n+' of '+cards.length+' shown';
 }
 q.addEventListener('input',apply); fp.addEventListener('change',apply);
 fs.addEventListener('change',apply); apply();
 var b=document.getElementById('tocbtn'),t=document.getElementById('toc');
 if(b&&t){b.addEventListener('click',function(){t.hidden=!t.hidden;});
  if(window.matchMedia('(max-width:1000px)').matches)t.hidden=true;}
})();
</script>
"""


def main() -> None:
    rows = list(csv.DictReader(CASES.open(encoding="utf-8-sig")))
    plan_md = PLAN.read_text()
    body, toc = render_markdown(plan_md)
    cases_html, subs, tally = render_cases(rows, suite_notes(plan_md))

    nav = []
    for sid, title in toc:
        nav.append(f'<li><a href="#{sid}">{html.escape(title)}</a>')
        if "@@CASES@@" in body.split(f'id="{sid}"')[1].split("<section")[0]:
            nav.append("<ul class='sub'>%s</ul>" % "".join(
                f'<li><a href="#{s}">{html.escape(t)}</a></li>' for s, t in subs))
        nav.append("</li>")

    pills = "".join(
        f'<i class="{STATUS_CLASS.get(k.lower(), "notrun")}">{html.escape(k)} {v}</i>'
        for k, v in sorted(tally.items()))

    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MiniCast — Manual Test Plan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS.read_text()}</style>
</head><body>
<header class="top"><div class="top-in"><b>MiniCast</b>
<span class="sep">Manual Test Plan</span>
<button class="tocbtn" id="tocbtn" aria-expanded="false" aria-controls="toc">Contents</button>
</div></header>
<div class="shell">
<nav class="toc" id="toc" aria-label="Contents"><ul>{"".join(nav)}</ul></nav>
<main><div class="pills">{pills}</div>
{body.replace("@@CASES@@", cases_html)}
</main></div>{JS}</body></html>"""

    OUT.write_text(page)
    print(f"{OUT.relative_to(ROOT)}: {len(page)//1024} KB, {len(rows)} cases, {len(toc)} sections")
    print("  status:", ", ".join(f"{k}={v}" for k, v in sorted(tally.items())))


if __name__ == "__main__":
    main()
