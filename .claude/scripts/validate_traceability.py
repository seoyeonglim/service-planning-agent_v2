#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
요구사항 추적성 자동 검증 스크립트 (서비스 기획 에이전트)

하는 일 (쉽게):
  기획서(PRD)에 정의한 요구사항(REQ)·엣지케이스(EC)·테스트(TC)가
  화면 명세/플로우/실제 화면(HTML)에 빠짐없이 연결됐는지 자동으로 대조한다.
  - "정의만 하고 안 쓴 것"(고아)과 "쓰는데 정의 안 된 것"(유령)을 찾아낸다.
  - MUST 요구사항인데 테스트(TC)가 없는 것을 찾아낸다.

단계 인식:
  - PRD만 있으면  → 내부 정합성(EC/TC ↔ REQ, MUST의 TC 커버리지)만 검사
  - ui/ 가 있으면 → REQ ↔ 화면 매핑까지 검사
  - screens/ 가 있으면 → 화면 HTML의 참조 유효성까지 검사

사용법:
  python3 validate_traceability.py [docs_dir] [--strict] [--report]
    docs_dir : 기본값 ./docs (하위 각 프로젝트를 모두 검사)
    --strict : 오류(❌)가 있으면 종료코드 2 (Phase 게이트/수동 검증용)
    --report : 프로젝트별 prd/_traceability_report.md 파일로도 저장

종료코드: 0=통과(또는 advisory), 2=--strict + 오류 있음
"""

import sys
import re
from pathlib import Path

PRIORITIES = ("MUST", "SHOULD", "NICE", "폐기")
# 우선순위 토큰: 셀 안에 다른 글자와 섞여 있어도("MUST·P1") 인식한다
PRIO_TOKEN_RE = re.compile(r"\b(MUST|SHOULD|NICE)\b|(폐기)")

# REQ-070·071·072·074, 010~016·020  /  REQ-090~093  /  REQ-001~005 형태를 통째로 잡는다
REF_RE = re.compile(r"(REQ|EC|TC|SC)-(\d+(?:~\d+)?(?:[·,]\s*\d+(?:~\d+)?)*)")
# TC-020-01 같은 복합 ID(향후 06_test_cases 스킬 포맷)는 먼저 따로 잡는다
TC_COMPOUND_RE = re.compile(r"TC-\d+-\d+")


def find_priority(cells):
    """ 표의 셀들에서 우선순위 토큰을 찾는다. 못 찾으면 UNKNOWN.
    (셀 전체 일치가 아니라 토큰 검색 — 'MUST·P1'·'**MUST**' 같은 표기도 인식) """
    for c in cells:
        m = PRIO_TOKEN_RE.search(c.replace("**", "").upper())
        if m:
            return m.group(1) or "폐기"
    return "UNKNOWN"


def expand_run(prefix, run):
    """ '070·071·072·074, 010~016' 같은 숫자 묶음을 개별 ID 집합으로 펼친다 """
    ids = set()
    for part in re.split(r"[·,]", run):
        part = part.strip()
        if not part:
            continue
        if "~" in part:
            a, b = part.split("~", 1)
            a, b = a.strip(), b.strip()
            if a.isdigit() and b.isdigit():
                width = len(a)
                for n in range(int(a), int(b) + 1):
                    ids.add(f"{prefix}-{str(n).zfill(width)}")
        elif part.isdigit():
            ids.add(f"{prefix}-{part}")
    return ids


def extract_refs_split(text):
    """ 참조 ID를 (명시 참조, 범위 전개 참조)로 나눠 추출.
    'REQ-001~005'처럼 범위(~)로만 걸린 중간 번호는 의도적 결번일 수 있어,
    유령 참조 판정 시 명시 참조(❌)와 범위 전개(⚠️)를 구분해야 오탐을 막는다. """
    explicit = {"REQ": set(), "EC": set(), "TC": set(), "SC": set()}
    ranged = {"REQ": set(), "EC": set(), "TC": set(), "SC": set()}
    for m in TC_COMPOUND_RE.finditer(text):
        explicit["TC"].add(m.group(0))
    cleaned = TC_COMPOUND_RE.sub(" ", text)
    for m in REF_RE.finditer(cleaned):
        prefix, run = m.group(1), m.group(2)
        for part in re.split(r"[·,]", run):
            part = part.strip()
            if not part:
                continue
            ids = expand_run(prefix, part)
            if "~" in part:
                a, b = (x.strip() for x in part.split("~", 1))
                ends = {f"{prefix}-{a}", f"{prefix}-{b}"} & ids
                explicit[prefix] |= ends
                ranged[prefix] |= ids - ends
            else:
                explicit[prefix] |= ids
    return explicit, ranged


def extract_refs(text):
    """ 텍스트에서 참조된 모든 ID를 종류별 집합으로 추출 (명시+범위 합집합) """
    explicit, ranged = extract_refs_split(text)
    return {k: explicit[k] | ranged[k] for k in explicit}


def registry_sections(prd_text):
    """ '요구사항 레지스트리' 헤딩 하위 본문만 이어 붙여 반환 (다음 동급 이상 헤딩 전까지).
    스코프 제외 표 등 다른 표의 REQ 행이 '선언'으로 오염되는 것을 막는다.
    헤딩이 없으면 None — 호출부에서 전체 텍스트로 폴백하고 경고한다. """
    lines = prd_text.splitlines()
    chunks, start, level = [], None, 0
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,4})\s", ln)
        if not m:
            continue
        if start is not None and len(m.group(1)) <= level:
            chunks.append("\n".join(lines[start:i]))
            start = None
        if start is None and "요구사항 레지스트리" in ln:
            start, level = i, len(m.group(1))
    if start is not None:
        chunks.append("\n".join(lines[start:]))
    return "\n".join(chunks) if chunks else None


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_declarations(prd_text, spec_text, reg_text):
    """ 선언(정의)된 ID들을 추출. REQ 선언은 레지스트리 섹션(reg_text)에서만 읽는다. """
    declared = {"REQ": {}, "EC": set(), "TC": set(), "SC": set()}

    # REQ: 레지스트리 표의 행  | REQ-001 | ... | MUST |  (**볼드** 표기 허용)
    for line in reg_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        rid = cells[0].replace("**", "").strip()
        if not re.fullmatch(r"REQ-\d+", rid):
            continue
        priority = find_priority(cells[1:])
        # 같은 REQ 행이 중복될 때(레지스트리 내 소표 등) 알려진 우선순위를
        # UNKNOWN이 덮어쓰지 않게 보존한다.
        if rid not in declared["REQ"] or declared["REQ"][rid] == "UNKNOWN":
            declared["REQ"][rid] = priority

    # EC: '### EC-01: ...' 헤딩
    for m in re.finditer(r"^#{2,4}\s*(EC-\d+)\b", prd_text, re.M):
        declared["EC"].add(m.group(1))

    # TC: '### TC-001 ...' 헤딩 (복합 ID 포함)
    for m in re.finditer(r"^#{2,4}\s*(TC-\d+(?:-\d+)?)\b", prd_text, re.M):
        declared["TC"].add(m.group(1))

    # SC: 화면 명세서의 '## 화면명: ... (SC-00)' + 인덱스 표
    for m in re.finditer(r"\(SC-\d+\)", spec_text):
        declared["SC"].add(m.group(0).strip("()"))
    for m in re.finditer(r"^\|\s*\d+\s*\|\s*(SC-\d+)\s*\|", spec_text, re.M):
        declared["SC"].add(m.group(1))

    return declared


def tc_links(prd_text):
    """ 각 TC가 어떤 REQ/EC를 검증하는지 매핑 (TC 헤딩의 괄호 안 참조) """
    req_to_tc, ec_to_tc = {}, {}
    pat = re.compile(r"^#{2,4}\s*(TC-\d+(?:-\d+)?)\s*\(([^)]*)\)", re.M)
    for m in pat.finditer(prd_text):
        tc = m.group(1)
        inner = extract_refs(m.group(2))
        for r in inner["REQ"]:
            req_to_tc.setdefault(r, set()).add(tc)
        for e in inner["EC"]:
            ec_to_tc.setdefault(e, set()).add(tc)
    return req_to_tc, ec_to_tc


class Report:
    def __init__(self, project):
        self.project = project
        self.lines = []
        self.errors = 0
        self.warns = 0

    def head(self, t):
        self.lines.append(f"\n■ {t}")

    def ok(self, t):
        self.lines.append(f"  ✅ {t}")

    def warn(self, t):
        self.warns += 1
        self.lines.append(f"  ⚠️  {t}")

    def err(self, t):
        self.errors += 1
        self.lines.append(f"  ❌ {t}")

    def info(self, t):
        self.lines.append(f"     {t}")


def fmt(ids):
    return ", ".join(sorted(ids))


def check_project(proj_dir):
    rep = Report(proj_dir.name)

    prd_dir = proj_dir / "prd"
    ui_dir = proj_dir / "ui"
    screens_dir = ui_dir / "screens"

    # 리포트(_*.md)·변경기록(CHANGELOG.md)은 PRD 본문이 아니다 — 함께 읽으면
    # 과거 CR이 인용한 옛 ID가 유령 참조로 오탐되고, 자기 리포트를 재섭취한다.
    prd_text = "\n".join(read(p) for p in sorted(prd_dir.glob("*.md"))
                         if not p.name.startswith("_") and p.name != "CHANGELOG.md")
    if not prd_text.strip():
        return None  # PRD 없으면 검사 대상 아님

    spec_path = ui_dir / "03_screen_spec.md"
    spec_text = read(spec_path)
    ui_docs_text = "\n".join(
        read(ui_dir / f)
        for f in ("01_information_architecture.md", "02_user_flow.md",
                  "03_screen_spec.md", "04_design_direction.md")
    )
    screens_text = "\n".join(read(p) for p in sorted(screens_dir.glob("*.html")))

    reg_text = registry_sections(prd_text)
    declared = parse_declarations(prd_text, spec_text, reg_text or prd_text)
    req_to_tc, ec_to_tc = tc_links(prd_text)

    req_ids = set(declared["REQ"])
    must = {r for r, p in declared["REQ"].items() if p == "MUST"}
    retired = {r for r, p in declared["REQ"].items() if p == "폐기"}
    unknown_prio = sorted(r for r, p in declared["REQ"].items() if p == "UNKNOWN")

    rep.head(f"선언 현황")
    rep.info(f"REQ {len(req_ids)}개 (MUST {len(must)}) · EC {len(declared['EC'])}개 · "
             f"TC {len(declared['TC'])}개 · SC {len(declared['SC'])}개")
    if reg_text is None:
        rep.warn("'요구사항 레지스트리' 헤딩을 찾지 못해 문서 전체에서 REQ 표를 인식함 "
                 "(스코프 제외 표 등이 선언으로 오염될 수 있음 — 헤딩을 추가하세요)")
    if unknown_prio:
        rep.warn(f"우선순위(MUST/SHOULD/NICE/폐기)를 인식하지 못한 REQ — "
                 f"TC 커버리지 검사에서 빠짐: {fmt(unknown_prio)}")

    # --- 1. PRD 내부 정합성: EC/TC가 가리키는 REQ가 실제로 정의됐는가 ---
    rep.head("PRD 내부 정합성")
    prd_exp, prd_rng = extract_refs_split(prd_text)
    prd_refs = {k: prd_exp[k] | prd_rng[k] for k in prd_exp}
    dangling_req = {r for r in prd_exp["REQ"] if r not in req_ids}
    if dangling_req:
        rep.err(f"PRD가 참조하지만 레지스트리에 없는 REQ(유령 참조): {fmt(dangling_req)}")
    else:
        rep.ok("PRD가 참조한 REQ는 모두 레지스트리에 정의됨")
    rng_gap = {r for r in prd_rng["REQ"] if r not in req_ids} - dangling_req
    if rng_gap:
        rep.warn(f"범위 참조(REQ-a~b) 전개에만 걸리고 레지스트리에 없는 번호 "
                 f"(의도적 결번인지 확인): {fmt(rng_gap)}")

    dangling_ec_ref = {e for e in prd_refs["EC"] if e not in declared["EC"]}
    if dangling_ec_ref:
        rep.warn(f"참조되지만 정의되지 않은 EC: {fmt(dangling_ec_ref)}")

    # --- 2. TC 커버리지: MUST REQ는 최소 1개 TC를 가져야 함 ---
    rep.head("TC 커버리지")
    if declared["TC"]:
        must_no_tc = sorted(r for r in must if not req_to_tc.get(r))
        covered = len(must) - len(must_no_tc)
        denom = len(must) if must else 1
        rep.info(f"MUST REQ TC 커버리지: {covered}/{len(must)} "
                 f"({round(covered/denom*100)}%)")
        if must_no_tc:
            rep.err(f"테스트(TC) 없는 MUST REQ: {fmt(must_no_tc)}")
        else:
            rep.ok("모든 MUST REQ가 1개 이상의 TC로 검증됨")

        ec_no_tc = sorted(e for e in declared["EC"] if not ec_to_tc.get(e))
        if ec_no_tc:
            rep.warn(f"테스트(TC) 없는 엣지케이스: {fmt(ec_no_tc)}")
    elif must:
        # TC가 0개면 'TC 없는 MUST' 검사 자체가 성립하지 않아 통과해 버린다 —
        # 검사할 수 없음(빈 서류함)과 검사해서 통과(확인된 서류함)를 구분한다.
        rep.err(f"PRD에 선언된 TC(`### TC-###`)가 하나도 없음 — "
                f"MUST REQ {len(must)}건 미검증 (06_test_cases 단계 수행 필요)")
    else:
        rep.warn("PRD에 선언된 TC(`### TC-###`)가 없음 — 06_test_cases 단계 미수행으로 보임")

    # --- 3. REQ ↔ 화면 매핑 (ui/ 존재 시) ---
    if ui_docs_text.strip():
        rep.head("REQ ↔ 화면/플로우 매핑 (Phase 2)")
        ui_exp, ui_rng = extract_refs_split(ui_docs_text)
        ui_refs = {k: ui_exp[k] | ui_rng[k] for k in ui_exp}
        mapped = ui_refs["REQ"] & req_ids
        orphan_must = sorted(r for r in must if r not in mapped)
        # 폐기 REQ는 화면에서 사라지는 것이 정상이므로 미매핑 경고 대상이 아니다
        orphan_other = sorted(r for r in (req_ids - must - retired)
                              if r not in ui_refs["REQ"])
        rep.info(f"화면/플로우에 매핑된 REQ: {len(mapped)}/{len(req_ids)}")
        if orphan_must:
            rep.err(f"어느 화면/플로우에도 없는 MUST REQ(누락 의심): {fmt(orphan_must)}")
        else:
            rep.ok("모든 MUST REQ가 화면/플로우에 매핑됨")
        if orphan_other:
            rep.warn(f"화면/플로우에 아직 없는 SHOULD/NICE REQ: {fmt(orphan_other)}")

        dangling_ui = {r for r in ui_exp["REQ"] if r not in req_ids}
        if dangling_ui:
            rep.err(f"화면 문서가 참조하지만 PRD에 없는 REQ: {fmt(dangling_ui)}")
        ui_rng_gap = {r for r in ui_rng["REQ"] if r not in req_ids} - dangling_ui
        if ui_rng_gap:
            rep.warn(f"화면 문서의 범위 참조 전개에만 걸리고 PRD에 없는 번호: {fmt(ui_rng_gap)}")

        # SC 참조 유효성
        dangling_sc = {s for s in ui_refs["SC"] if s not in declared["SC"]}
        if dangling_sc:
            rep.warn(f"참조되지만 화면 명세에 정의되지 않은 SC: {fmt(dangling_sc)}")
    else:
        rep.head("REQ ↔ 화면 매핑")
        rep.info("ui/ 문서 미작성 — Phase 2 진입 전이므로 건너뜀")

    # --- 4. 화면 HTML 참조 유효성 (screens/ 존재 시) ---
    if screens_text.strip():
        rep.head("화면 HTML 참조 유효성 (Phase 3)")
        sc_exp, sc_rng = extract_refs_split(screens_text)
        dangling_html = {r for r in sc_exp["REQ"] if r not in req_ids}
        if dangling_html:
            rep.err(f"화면 HTML이 참조하지만 PRD에 없는 REQ: {fmt(dangling_html)}")
        else:
            rep.ok("화면 HTML의 REQ 참조가 모두 유효함")
        html_rng_gap = {r for r in sc_rng["REQ"] if r not in req_ids} - dangling_html
        if html_rng_gap:
            rep.warn(f"화면 HTML의 범위 참조 전개에만 걸리고 PRD에 없는 번호: {fmt(html_rng_gap)}")
        n_screens = len(list(screens_dir.glob("*.html")))
        rep.info(f"생성된 화면 HTML: {n_screens}개")

    return rep


def main():
    argv = sys.argv[1:]
    strict = "--strict" in argv
    write_report = "--report" in argv
    positional = [a for a in argv if not a.startswith("--")]
    docs_dir = Path(positional[0]) if positional else Path("docs")

    if not docs_dir.is_dir():
        # 훅에서 docs가 아직 없을 수 있음 → 조용히 통과
        print("ℹ️  docs/ 폴더가 없어 추적성 검사를 건너뜁니다.")
        return 0

    projects = [d for d in sorted(docs_dir.iterdir())
                if d.is_dir() and not d.name.startswith(".")]
    if not projects:
        print("ℹ️  검사할 프로젝트가 없습니다.")
        return 0

    total_err = total_warn = 0
    out = ["═" * 50, "  요구사항 추적성 자동 검증", "═" * 50]

    for proj in projects:
        rep = check_project(proj)
        if rep is None:
            continue
        out.append(f"\n🗂  [{rep.project}]")
        out.extend(rep.lines)
        status = "❌ 오류 있음" if rep.errors else ("⚠️  경고 있음" if rep.warns else "✅ 통과")
        out.append(f"  └─ 결과: {status} (오류 {rep.errors} · 경고 {rep.warns})")
        total_err += rep.errors
        total_warn += rep.warns

        if write_report:
            rpt_path = proj / "prd" / "_traceability_report.md"
            if rpt_path.parent.is_dir():
                block = "\n".join(rep.lines).lstrip("\n")
                body = (f"# 요구사항 추적성 검증 리포트\n\n"
                        f"- 대상: {rep.project}\n"
                        f"- 결과: 오류 {rep.errors} · 경고 {rep.warns}\n\n"
                        f"```\n{block}\n```\n")
                rpt_path.write_text(body, encoding="utf-8")

    out.append("\n" + "─" * 50)
    out.append(f"총계: 오류 {total_err} · 경고 {total_warn}")
    if total_err:
        out.append("👉 ❌ 오류 항목을 보완한 뒤 다음 단계로 진행하세요.")
    print("\n".join(out))

    return 2 if (strict and total_err) else 0


if __name__ == "__main__":
    sys.exit(main())
