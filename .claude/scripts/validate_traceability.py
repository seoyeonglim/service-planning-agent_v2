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

PRIORITIES = ("MUST", "SHOULD", "NICE")

# REQ-070·071·072·074, 010~016·020  /  REQ-090~093  /  REQ-001~005 형태를 통째로 잡는다
REF_RE = re.compile(r"(REQ|EC|TC|SC)-(\d+(?:~\d+)?(?:[·,]\s*\d+(?:~\d+)?)*)")
# TC-020-01 같은 복합 ID(향후 06_test_cases 스킬 포맷)는 먼저 따로 잡는다
TC_COMPOUND_RE = re.compile(r"TC-\d+-\d+")


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


def extract_refs(text):
    """ 텍스트에서 참조된 모든 ID를 종류별 집합으로 추출 """
    refs = {"REQ": set(), "EC": set(), "TC": set(), "SC": set()}
    for m in TC_COMPOUND_RE.finditer(text):
        refs["TC"].add(m.group(0))
    cleaned = TC_COMPOUND_RE.sub(" ", text)
    for m in REF_RE.finditer(cleaned):
        prefix, run = m.group(1), m.group(2)
        refs[prefix] |= expand_run(prefix, run)
    return refs


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_declarations(prd_text, spec_text):
    """ 선언(정의)된 ID들을 추출 """
    declared = {"REQ": {}, "EC": set(), "TC": set(), "SC": set()}

    # REQ: 4장 레지스트리 표의 행  | REQ-001 | ... | MUST |
    for line in prd_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        m = re.fullmatch(r"REQ-\d+", cells[0])
        if not m:
            continue
        priority = next((c.upper() for c in cells if c.upper() in PRIORITIES), "UNKNOWN")
        # 레지스트리(§4)가 정한 우선순위를, 뒤따르는 추적표(§15)의 단일 REQ 행이 UNKNOWN으로
        # 덮어쓰지 않게 한다. (추적표 행도 "| REQ-### | ..."로 시작해 선언으로 잡히지만
        # 우선순위 칸이 없어 UNKNOWN이 되므로, 알려진 값이 있으면 보존한다.)
        if cells[0] not in declared["REQ"] or declared["REQ"][cells[0]] == "UNKNOWN":
            declared["REQ"][cells[0]] = priority

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

    prd_text = "\n".join(read(p) for p in sorted(prd_dir.glob("*.md")))
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

    declared = parse_declarations(prd_text, spec_text)
    req_to_tc, ec_to_tc = tc_links(prd_text)

    req_ids = set(declared["REQ"])
    must = {r for r, p in declared["REQ"].items() if p == "MUST"}

    rep.head(f"선언 현황")
    rep.info(f"REQ {len(req_ids)}개 (MUST {len(must)}) · EC {len(declared['EC'])}개 · "
             f"TC {len(declared['TC'])}개 · SC {len(declared['SC'])}개")

    # --- 1. PRD 내부 정합성: EC/TC가 가리키는 REQ가 실제로 정의됐는가 ---
    rep.head("PRD 내부 정합성")
    prd_refs = extract_refs(prd_text)
    dangling_req = {r for r in prd_refs["REQ"] if r not in req_ids}
    if dangling_req:
        rep.err(f"PRD가 참조하지만 레지스트리에 없는 REQ(유령 참조): {fmt(dangling_req)}")
    else:
        rep.ok("PRD가 참조한 REQ는 모두 레지스트리에 정의됨")

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
    else:
        rep.warn("PRD에 선언된 TC(`### TC-###`)가 없음 — 06_test_cases 단계 미수행으로 보임")

    # --- 3. REQ ↔ 화면 매핑 (ui/ 존재 시) ---
    if ui_docs_text.strip():
        rep.head("REQ ↔ 화면/플로우 매핑 (Phase 2)")
        ui_refs = extract_refs(ui_docs_text)
        mapped = ui_refs["REQ"] & req_ids
        orphan_must = sorted(r for r in must if r not in mapped)
        orphan_other = sorted(r for r in (req_ids - must) if r not in ui_refs["REQ"])
        rep.info(f"화면/플로우에 매핑된 REQ: {len(mapped)}/{len(req_ids)}")
        if orphan_must:
            rep.err(f"어느 화면/플로우에도 없는 MUST REQ(누락 의심): {fmt(orphan_must)}")
        else:
            rep.ok("모든 MUST REQ가 화면/플로우에 매핑됨")
        if orphan_other:
            rep.warn(f"화면/플로우에 아직 없는 SHOULD/NICE REQ: {fmt(orphan_other)}")

        dangling_ui = {r for r in ui_refs["REQ"] if r not in req_ids}
        if dangling_ui:
            rep.err(f"화면 문서가 참조하지만 PRD에 없는 REQ: {fmt(dangling_ui)}")

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
        sc_refs = extract_refs(screens_text)
        dangling_html = {r for r in sc_refs["REQ"] if r not in req_ids}
        if dangling_html:
            rep.err(f"화면 HTML이 참조하지만 PRD에 없는 REQ: {fmt(dangling_html)}")
        else:
            rep.ok("화면 HTML의 REQ 참조가 모두 유효함")
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
