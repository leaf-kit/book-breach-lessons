"""원고 점검 — 차례 대조, 분량, 표기, 사실 ID"""
import re, os, glob, sys, collections

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

md = open('README.md', encoding='utf-8').read()
lines = md.split('\n')
start = next((i for i, l in enumerate(lines)
              if re.match(r'^##\s+차례\s*$', l.strip())), -1)
toc = []
for l in lines[start + 1:]:
    if re.match(r'^##\s', l):
        break
    m = re.match(r'^\s*-\s+\[(.+?)\]\(([^)]+)\)\s*$', l)
    if m and re.search(r'\.md(#|$)', m.group(2)):
        toc.append((m.group(1), m.group(2)))

print("=== 차례 대조")
print("차례 항목 %d개" % len(toc))
missing = [p for _, p in toc if not os.path.exists(p)]
print("차례에 있는데 파일 없음:", missing or "없음")
listed = {p for _, p in toc}
allmd = set(glob.glob('part*/*.md')) | set(glob.glob('appendix/*.md'))
print("파일은 있는데 차례에 없음:", sorted(allmd - listed) or "없음")

print()
print("=== 분량 (1쪽 = 650자)")
total = 0
rows = []
for _, p in toc:
    t = open(p, encoding='utf-8').read()
    t = re.sub(r'```.*?```', '', t, flags=re.S)
    t = re.sub(r'[#>|\-*`\[\]()_]', '', t)
    n = len(re.sub(r'\s', '', t))
    total += n
    rows.append((p, n))
for p, n in rows:
    print("  %-34s %6d  %5.1f쪽" % (p, n, n / 650))
print("  %-34s %6d  %5.1f쪽" % ("합계", total, total / 650))

print()
print("=== 표기 점검")
banned = ['의 중요성은 아무리', '급변하는 디지털', '과언이 아닙', '다양한 측면에서',
          '시사하는 바가', '되어진다', '라고 할 수 있습니다', '인 것입니다',
          '하도록 합니다', '에 있어서']
hits = collections.Counter()
for p in sorted(allmd):
    t = open(p, encoding='utf-8').read()
    for w in banned:
        if w in t:
            hits[(p, w)] = t.count(w)
    if '·' in t:
        hits[(p, '가운데점')] = t.count('·')
    if '!' in re.sub(r'`[^`]*`|```.*?```', '', t, flags=re.S):
        hits[(p, '느낌표')] = 1
if hits:
    for (p, w), c in hits.items():
        print("  %-34s %-12s %d" % (p, w, c))
else:
    print("  걸린 것 없음")

print()
print("=== 문장 길이 (상한 60자)")
long_sents = []
for p in sorted(allmd):
    t = open(p, encoding='utf-8').read()
    t = re.sub(r'```.*?```', '', t, flags=re.S)       # 코드 블록 제외
    for ln, line in enumerate(t.split('\n'), 1):
        s = line.strip()
        if not s or s.startswith(('#', '|', '>', '-', '*', '```', '<')):
            continue                                   # 제목, 표, 인용, 목록, 원시 HTML 제외
        for sent in re.split(r'(?<=다\.)\s+|(?<=요\.)\s+', s):
            plain = re.sub(r'[`*_\[\]()]', '', sent).strip()
            n = len(re.sub(r'\s', '', plain))
            if n > 60:
                long_sents.append((p, ln, n, plain[:40]))
if long_sents:
    print("  %d곳" % len(long_sents))
    for p, ln, n, head in long_sents[:30]:
        print("  %-30s %4d행 %3d자  %s…" % (p, ln, n, head))
    if len(long_sents) > 30:
        print("  ... 그 밖 %d곳" % (len(long_sents) - 30))
else:
    print("  걸린 것 없음")

print()
print("=== 사실 ID")
facts = open('research/facts.yaml', encoding='utf-8').read()
declared = set(re.findall(r'^\s*-\s+id:\s+(F-\d+)', facts, re.M))
labels = collections.Counter(re.findall(r'^\s*label:\s*(\S+)', facts, re.M))
print("  등록된 사실: %d건" % len(declared))
print("  라벨:", dict(labels))

used = set()
for p in sorted(allmd):
    used |= set(re.findall(r'F-\d+', open(p, encoding='utf-8').read()))
print("  본문에서 인용한 ID: %d개" % len(used))
print("  본문에 있는데 미등록:", sorted(used - declared) or "없음")
print("  등록됐는데 본문 미사용:", sorted(declared - used) or "없음")
