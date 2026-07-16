#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화면 인덱스 자동 생성 스크립트 (서비스 기획 에이전트)

하는 일 (쉽게):
  프로젝트의 화면 HTML(ui/screens/*.html)이 늘어나면, 개발자·리뷰어가
  "무슨 화면이 몇 개고 어디 있는지"를 한눈에 볼 문서가 필요하다.
  이 스크립트는 화면 HTML의 추적 꼬리표(1줄차 주석)와 화면 명세서의
  화면 목록 표를 읽어 **ui/screens/index.html** 을 자동 생성한다.
  - 화면별 미리보기(iframe) + SC-ID·구분·우선순위·화면명
  - 추적 꼬리표(REQ·TC)
  - 링크 4종: 본 HTML · 와이어프레임 · 주석 도해 · 화면 명세
  - 명세에는 있는데 본 HTML이 아직 없는 화면은 '미생성'으로 표시

  ⚠️ index.html은 자동 생성물 — 직접 수정 금지(재생성 시 덮어씀).
  검증기(validate/consistency)는 index.html을 화면으로 취급하지 않는다.

사용법:
  python3 .claude/scripts/generate_screen_index.py [docs_dir|프로젝트_dir]
    docs_dir      : 기본값 ./docs — 하위 각 프로젝트를 모두 생성
    프로젝트_dir  : docs/[프로젝트명] 하나만 지정해 그 프로젝트만 생성
  화면 HTML(ui/screens/*.html)이 없는 프로젝트는 건너뛴다.

종료코드: 0=정상 (생성 대상 없음 포함)
"""

import html as html_mod
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_traceability import find_priority, read

INDEX_NAME = "index.html"

# 화면 HTML 1줄차 추적 꼬리표: <!-- SC-## | 화면명 | REQ-### | TC-### -->
# (TC 세그먼트는 아직 TC가 안 걸린 화면도 있어 선택 항목으로 인식)
TAG_RE = re.compile(r"<!--\s*(SC-\d+)\s*\|([^|]*)\|([^|]*?)(?:\|([^>]*?))?-->")


def sc_num(sc_id):
    return int(sc_id.split("-")[1])


def esc(text):
    return html_mod.escape(str(text), quote=True)


def parse_screen_html(path):
    """ 화면 HTML에서 추적 꼬리표(SC-ID·화면명·REQ·TC)를 읽는다. """
    t = read(path)
    m = TAG_RE.search(t)
    if not m:
        return None
    return {
        "sc": m.group(1),
        "title": m.group(2).strip(),
        "req": m.group(3).strip(),
        "tc": (m.group(4) or "").strip().rstrip("- ").strip(),
    }


def parse_spec_table(spec_text):
    """ 화면 명세서의 화면 목록 표에서 (표 순서, 구분, 화면명, 우선순위)를 읽는다.
    열 구성이 프로젝트마다 조금 달라도 되도록 SC 셀 위치 기준으로 상대 해석한다. """
    rows = {}
    for line in spec_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.replace("**", "").strip() for c in s.strip("|").split("|")]
        sc_idx = next((i for i, c in enumerate(cells)
                       if re.fullmatch(r"SC-\d+", c)), None)
        if sc_idx is None:
            continue
        sc = cells[sc_idx]
        if sc in rows:
            continue  # 첫 등장(화면 목록 표)만 정본으로 쓴다
        rows[sc] = {
            "order": len(rows),
            "kind": cells[sc_idx + 1] if len(cells) > sc_idx + 1 else "",
            "name": cells[sc_idx + 2] if len(cells) > sc_idx + 2 else "",
            "priority": find_priority(cells[sc_idx + 1:]),
        }
    return rows


def wf_links(wf_dir, n):
    """ 와이어프레임 폴더에서 화면 번호 n의 wf-/annotated- 파일을 찾는다.
    (wf-SC-01-*, wf-admin-sc-07-* 등 표기 편차를 숫자 경계 비교로 흡수) """
    pat = re.compile(rf"sc-0*{n}(?!\d)", re.I)
    wf, annot = [], []
    for p in sorted(wf_dir.glob("*.html")) if wf_dir.is_dir() else []:
        if not pat.search(p.name):
            continue
        (annot if p.name.startswith("annotated-") else wf).append(p.name)
    return wf, annot


CSS = """
:root{--ink:#1F2937;--sub:#6B7280;--line:#E5E7EB;--bg:#F8FAFC;--card:#fff;
--chip:#F3F4F6;--must:#DC2626;--should:#D97706;--nice:#2563EB;--off:#9CA3AF;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Pretendard',system-ui,-apple-system,sans-serif;background:var(--bg);
color:var(--ink);padding:32px 24px;max-width:1360px;margin:0 auto}
header h1{font-size:22px;font-weight:700}
header p{color:var(--sub);font-size:13px;margin-top:6px;line-height:1.6}
.controls{margin:16px 0 20px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.controls button{font:600 12px/1 inherit;padding:8px 14px;border:1px solid var(--line);
border-radius:8px;background:var(--card);cursor:pointer;color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
overflow:hidden;display:flex;flex-direction:column}
.thumb{position:relative;height:190px;background:#EEF2F7;overflow:hidden;display:block}
.thumb iframe{width:1280px;height:812px;transform:scale(0.234);transform-origin:0 0;
border:0;pointer-events:none}
.thumb .empty{display:flex;height:100%;align-items:center;justify-content:center;
color:var(--off);font-size:13px;font-weight:600}
body.no-preview .thumb{display:none}
.meta{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.rowline{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.sc{font:700 12px/1 inherit;background:var(--ink);color:#fff;border-radius:6px;padding:4px 7px}
.chip{font:600 11px/1 inherit;background:var(--chip);color:var(--sub);
border-radius:9999px;padding:4px 8px}
.chip.MUST{background:#FEE2E2;color:var(--must)}
.chip.SHOULD{background:#FEF3C7;color:var(--should)}
.chip.NICE{background:#DBEAFE;color:var(--nice)}
.chip.폐기,.chip.제외{background:var(--chip);color:var(--off);text-decoration:line-through}
h2.name{font-size:15px;font-weight:700}
.trace{font-size:11px;color:var(--sub);line-height:1.6;word-break:break-all}
.links{margin-top:auto;padding-top:8px;border-top:1px dashed var(--line);
display:flex;gap:10px;flex-wrap:wrap;font-size:12px}
.links a{color:#0F766E;font-weight:600;text-decoration:none}
.links a:hover{text-decoration:underline}
.links .none{color:var(--off);font-weight:600}
footer{margin-top:28px;color:var(--off);font-size:11px;line-height:1.7}
"""


def render_card(row):
    sc = row.get("sc")
    if not sc:  # 추적 꼬리표 없는 화면 — 파일명만으로 수록(누락 방지)
        return f"""<article class="card">
  <a class="thumb" href="{esc(row['file'])}" target="_blank" rel="noopener">
  <iframe src="{esc(row['file'])}" loading="lazy" tabindex="-1"></iframe></a>
  <div class="meta">
    <h2 class="name">{esc(row['file'])}</h2>
    <p class="trace">⚠️ 추적 꼬리표(SC-ID 주석) 없음 — 스킬 11의 2줄 주석 규칙 적용 필요</p>
    <div class="links"><a href="{esc(row['file'])}" target="_blank" rel="noopener">본 HTML</a></div>
  </div>
</article>"""
    n = sc_num(sc)
    pr = row.get("priority") or ""
    pr_cls = pr if pr in ("MUST", "SHOULD", "NICE", "폐기", "제외") else ""
    chips = [f'<span class="sc">{esc(sc)}</span>']
    if row.get("kind"):
        chips.append(f'<span class="chip">{esc(row["kind"])}</span>')
    if pr:
        chips.append(f'<span class="chip {esc(pr_cls)}">{esc(pr)}</span>')

    if row.get("file"):
        thumb = (f'<a class="thumb" href="{esc(row["file"])}" target="_blank" rel="noopener">'
                 f'<iframe src="{esc(row["file"])}" loading="lazy" tabindex="-1"></iframe></a>')
        main_link = f'<a href="{esc(row["file"])}" target="_blank" rel="noopener">본 HTML</a>'
    else:
        thumb = '<div class="thumb"><div class="empty">본 HTML 미생성</div></div>'
        main_link = '<span class="none">본 HTML 미생성</span>'

    links = [main_link]
    for label, names in (("와이어프레임", row["wf"]), ("주석 도해", row["annot"])):
        if names:
            links.append(f'<a href="../../assets/wireframes/{esc(names[0])}" '
                         f'target="_blank" rel="noopener">{label}</a>')
    links.append(f'<a href="../03_screen_spec.md" target="_blank">명세 ({esc(sc)})</a>')

    trace = []
    if row.get("req"):
        trace.append(f"REQ: {esc(row['req'])}")
    if row.get("tc"):
        trace.append(f"TC: {esc(row['tc'])}")

    return f"""<article class="card" id="sc-{n}">
  {thumb}
  <div class="meta">
    <div class="rowline">{''.join(chips)}</div>
    <h2 class="name">{esc(row.get('name') or row.get('title') or '')}</h2>
    <p class="trace">{' · '.join(trace)}</p>
    <div class="links">{' '.join(links)}</div>
  </div>
</article>"""


def build_index(proj_dir):
    screens_dir = proj_dir / "ui" / "screens"
    wf_dir = proj_dir / "assets" / "wireframes"
    files = [p for p in sorted(screens_dir.glob("*.html")) if p.name != INDEX_NAME]
    if not files:
        return None

    spec_rows = parse_spec_table(read(proj_dir / "ui" / "03_screen_spec.md"))

    rows, no_tag = {}, []
    for p in files:
        parsed = parse_screen_html(p)
        if not parsed:
            no_tag.append(p.name)
            continue
        parsed["file"] = p.name
        rows[parsed["sc"]] = parsed
    for sc, info in spec_rows.items():  # 명세에만 있는 화면(미생성) 포함
        rows.setdefault(sc, {"sc": sc, "req": "", "tc": "", "file": None})
        rows[sc].update({k: v for k, v in info.items() if v})

    for sc, row in rows.items():
        row["wf"], row["annot"] = wf_links(wf_dir, sc_num(sc))
    ordered = sorted(rows.values(), key=lambda r: (r.get("order", 999), sc_num(r["sc"])))
    # 꼬리표 없는 화면도 파일명 카드로 수록 — 인덱스에서 화면이 사라지는 일은 없어야 한다
    ordered += [{"sc": None, "file": name} for name in no_tag]

    built = sum(1 for r in ordered if r.get("file"))
    cards = "\n".join(render_card(r) for r in ordered)
    doc = f"""<!DOCTYPE html>
<!-- 자동 생성: .claude/scripts/generate_screen_index.py — 직접 수정 금지(재생성 시 덮어씀) -->
<!-- 재생성: python3 .claude/scripts/generate_screen_index.py docs/{esc(proj_dir.name)} -->
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>화면 인덱스 — {esc(proj_dir.name)}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>화면 인덱스 · {esc(proj_dir.name)}</h1>
  <p>화면 {len(ordered)}개 (본 HTML {built}개 생성) · {date.today().isoformat()} 자동 생성 —
  카드의 미리보기·링크로 본 HTML / 와이어프레임 / 주석 도해 / 화면 명세를 오간다.
  SC-ID가 조인 키(자세한 규칙: <a href="../03_screen_spec.md">03_screen_spec.md</a>).</p>
</header>
<div class="controls">
  <button onclick="document.body.classList.toggle('no-preview')">미리보기 켜기/끄기</button>
</div>
<div class="grid">
{cards}
</div>
<footer>이 문서는 자동 생성물입니다 — 화면 HTML을 만들거나 수정한 뒤
<code>python3 .claude/scripts/generate_screen_index.py</code> 로 재생성하세요.</footer>
</body>
</html>
"""
    (screens_dir / INDEX_NAME).write_text(doc, encoding="utf-8")
    return len(ordered), built, no_tag


def main():
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = Path(positional[0]) if positional else Path("docs")
    if not target.is_dir():
        print(f"ℹ️  폴더가 없습니다: {target}")
        return 0

    # 단일 프로젝트 폴더 지정도 허용 (ui/screens 보유 여부로 판별)
    projects = [target] if (target / "ui" / "screens").is_dir() else [
        d for d in sorted(target.iterdir()) if d.is_dir() and not d.name.startswith(".")
    ]

    made = 0
    for proj in projects:
        res = build_index(proj)
        if res is None:
            continue
        total, built, no_tag = res
        made += 1
        print(f"✅ [{proj.name}] ui/screens/{INDEX_NAME} 생성 — 화면 {total}개 (본 HTML {built}개)")
        if no_tag:
            print(f"   ⚠️ 추적 꼬리표(1줄차 주석) 없는 화면 HTML — 파일명으로만 수록: {', '.join(no_tag)}")
    if not made:
        print("ℹ️  화면 HTML(ui/screens/*.html)이 있는 프로젝트가 없어 생성할 인덱스가 없습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
