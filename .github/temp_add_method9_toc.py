from pathlib import Path
import re

p = Path('09-06-26-10-24_Azure_Front_Door_Application_Gateway_WAF_Method_9_Deep_Dive.md')
s = p.read_text()

if '## Table of contents' in s:
    raise SystemExit('TOC already present')

headings = []
in_fence = False
slug_counts = {}
for line in s.splitlines():
    if line.startswith('```'):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    m = re.match(r'^(#{1,2})\s+(.+?)\s*$', line)
    if not m:
        continue
    level = len(m.group(1))
    title = m.group(2).strip()
    if title == 'Azure Front Door WAF and Application Gateway WAF — Method 9 Deep Dive':
        continue
    if title == 'Table of contents':
        continue
    # GitHub-like slug: lowercase; drop punctuation except hyphen/space/word chars; spaces -> hyphen.
    slug = title.lower()
    slug = re.sub(r'[^\w\- ]', '', slug, flags=re.UNICODE)
    slug = slug.replace(' ', '-')
    base = slug
    n = slug_counts.get(base, 0)
    if n:
        slug = f'{base}-{n}'
    slug_counts[base] = n + 1
    headings.append((level, title, slug))

lines = ['## Table of contents', '']
for level, title, slug in headings:
    indent = '  ' if level == 2 else ''
    lines.append(f'{indent}- [{title}](#{slug})')
lines += ['', '---', '']
toc = '\n'.join(lines)

anchor = '# 1. What Method 9 actually is\n'
if anchor not in s:
    raise SystemExit('Main section anchor not found')
s = s.replace(anchor, toc + anchor, 1)
p.write_text(s)
