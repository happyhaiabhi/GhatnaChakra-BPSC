#!/usr/bin/env python3
"""Build a standalone styled HTML preview of the Phase 2 deliverables. No deps."""
import re, csv, html

def esc(s):
    return html.escape(s)

def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s

def md_to_html(md):
    lines = md.split('\n')
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|$', lines[i+1]):
            hdr = [c.strip() for c in ln.strip().strip('|').split('|')]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in hdr) + '</tr></thead><tbody>')
            i += 2
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells) + '</tr>')
                i += 1
            out.append('</tbody></table>')
            continue
        if ln.startswith('### '):
            out.append(f'<h3>{inline(ln[4:])}</h3>'); i += 1; continue
        if ln.startswith('## '):
            out.append(f'<h2>{inline(ln[3:])}</h2>'); i += 1; continue
        if ln.startswith('# '):
            out.append(f'<h1>{inline(ln[2:])}</h1>'); i += 1; continue
        if ln.startswith('> '):
            out.append(f'<blockquote>{inline(ln[2:])}</blockquote>'); i += 1; continue
        if ln.strip() == '---':
            out.append('<hr/>'); i += 1; continue
        if ln.startswith('- ') or re.match(r'^\d+\. ', ln):
            items = []
            while i < len(lines) and (lines[i].startswith('- ') or re.match(r'^\d+\. ', lines[i])):
                items.append(re.sub(r'^(\-|\d+\.) ', '', lines[i]))
                i += 1
            tag = 'ol' if re.match(r'^\d+\. ', lines[i-1]) else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
            continue
        if ln.strip() == '':
            i += 1; continue
        out.append(f'<p>{inline(ln)}</p>'); i += 1
    return '\n'.join(out)

CSS = """body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1000px;margin:0 auto;
padding:24px;color:#1a1a1a;background:#fff;line-height:1.6}h1{font-size:1.7em;border-bottom:3px solid #1a5fb4;
padding-bottom:8px}h2{font-size:1.3em;color:#1a5fb4;margin-top:1.8em;border-bottom:1px solid #ddd;
padding-bottom:4px}h3{font-size:1.05em}table{border-collapse:collapse;width:100%;margin:12px 0;font-size:.9em}
th,td{border:1px solid #ccc;padding:6px 8px;text-align:left}th{background:#f0f4f8}tr:nth-child(even)td{background:#fafbfc}
code{background:#f0f0f0;padding:1px 5px;border-radius:4px;font-size:.88em}blockquote{background:#fff8e1;
border-left:4px solid #f0b429;padding:8px 14px;margin:12px 0}.nav{position:sticky;top:0;background:#1a5fb4;
color:#fff;padding:10px 16px;border-radius:8px;margin-bottom:16px;font-size:.95em}.nav a{color:#fff;margin-right:14px}
.toc{background:#f5f7fa;border:1px solid #ddd;border-radius:8px;padding:12px 20px;margin:16px 0}
.toc a{display:inline-block;margin:2px 10px 2px 0;font-size:.9em;color:#1a5fb4}"""

report = open('docs/PYQ_PHASE2_REPORT.md').read()
appb = open('docs/PYQ_PHASE2_APPENDIX_B.md').read()

# anchorize h2s for TOC
def with_anchors(md):
    md = re.sub(r'^## (§\d+.*)$', lambda m: f"## <a id=\"{m.group(1).split(' ')[0]}\"></a>{m.group(1)}", md, flags=re.M)
    return md

report_html = md_to_html(with_anchors(report))
appb_html = md_to_html(appb)
toc = ' '.join(f'<a href="#§{n}">§{n}</a>' for n in range(1, 25))

page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>PYQ Phase 2 — Report Preview</title><style>{CSS}</style></head><body>
<div class="nav"><strong>PYQ Phase 2 deliverables</strong> &nbsp;
<a href="#report">Report (§24)</a><a href="#appb">Appendix B</a>
<a href="docs/PYQ_PHASE2_APPENDIX_A.csv">Appendix A (CSV)</a>
<a href="data/pyq_phase2_calibrated_top100.json">Top-100 (JSON)</a>
<a href="data/pyq_phase2_overrides.json">Overrides (JSON)</a></div>
<div id="report">{report_html}</div>
<div class="toc"><strong>Jump to:</strong> {toc}</div>
<hr/><div id="appb">{appb_html}</div>
</body></html>"""
open('preview.html', 'w').write(page)
print("preview.html written", len(page), "bytes")
