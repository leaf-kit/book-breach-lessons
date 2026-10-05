"""출처 링크 점검 — facts.yaml 의 source_url 이 아직 살아 있는지 본다.

보안 책에서 링크가 죽는 것은 시간문제다. 기사는 내려가고 기관은 주소를 바꾼다.
죽은 링크를 그대로 두면 독자가 근거를 못 보고, 못 보면 책을 의심한다.

쓰는 법
    python3 tools/linkcheck.py

읽는 법
    200, 403  정상. 403 은 봇 차단이라 사람 브라우저에서는 대개 열린다
    404, 410  원문이 내려갔다. source_url 을 비우고 dead_url 로 옮긴다
    000       접속 실패. 일시적일 수 있으니 한 번 더 돌려 본다
"""
import re, os, subprocess, sys
import concurrent.futures as cf

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0 Safari/537.36')

text = open('research/facts.yaml', encoding='utf-8').read()
facts = re.findall(r'-\s+id:\s+(F-\d+)\s*\n(.*?)(?=\n\s*-\s+id:|\n# |\Z)', text, re.S)

targets, blank = [], []
for fid, body in facts:
    m = re.search(r'source_url:\s*"([^"]*)"', body)
    url = m.group(1).strip() if m else ''
    if url:
        targets.append((fid, url))
    else:
        blank.append(fid)


def check(item):
    fid, url = item
    r = subprocess.run(
        ['curl', '-s', '-o', os.devnull, '-w', '%{http_code}', '-L',
         '--max-time', '20', '-A', UA, '-H', 'Accept: text/html', url],
        capture_output=True, text=True)
    return fid, url, r.stdout.strip()


with cf.ThreadPoolExecutor(8) as ex:
    rows = sorted(ex.map(check, targets))

ok   = [r for r in rows if r[2] == '200']
soft = [r for r in rows if r[2] == '403']          # 봇 차단
dead = [r for r in rows if r[2] not in ('200', '403')]

print("=== 출처 링크 점검")
print("  등록된 사실 %d건" % len(facts))
print("  링크 있음 %d건 / 비워 둔 것 %d건" % (len(targets), len(blank)))
print("  정상 %d / 봇 차단 %d / 확인 필요 %d" % (len(ok), len(soft), len(dead)))

if blank:
    print()
    print("  링크를 비워 둔 사실 (대체 출처를 찾는 중):")
    for fid in blank:
        print("    %s" % fid)

if soft:
    print()
    print("  403 — 봇 차단. 브라우저에서 직접 확인한다:")
    for fid, url, code in soft:
        print("    %-7s %s" % (fid, url[:92]))

if dead:
    print()
    print("  확인 필요 — 내려갔으면 source_url 을 비우고 dead_url 로 옮긴다:")
    for fid, url, code in dead:
        print("    %-7s %-4s %s" % (fid, code, url[:88]))

sys.exit(1 if dead else 0)
