#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
내용 정합성 자동 검증 스크립트 (서비스 기획 에이전트)

하는 일 (쉽게):
  추적성 검증(validate_traceability.py)이 "ID 연결이 끊겼나"를 본다면,
  이 스크립트는 **ID는 멀쩡한데 문서끼리 다른 말을 하는 곳** 중
  기계가 확실히 판정할 수 있는 것만 골라 검사한다.
  - 기능명세서(FS)의 우선순위가 근거 REQ에서 제대로 상속됐나
  - FS의 추진 단계(P1~)가 REQ 레지스트리의 단계와 일치하나
  - 모든 MUST FS가 WBS에 배치됐나
  - 화면(SC)마다 와이어프레임·본 HTML 산출물이 존재하나
  - 화면 HTML이 명세·주석도해로 상호 링크되고, 가리키는 주석도해가 실재하나
  - 폐기된 REQ가 활성 문서에서 여전히 참조되나
  - 같은 FS ID가 두 번 선언되지 않았나

  ⚠️ 문장의 의미가 서로 어긋나는지(예: PRD "3초" vs FS "5초")는 기계로 판정 불가 —
  그건 스킬 15(내용 정합성 검증)의 에이전트 의미 대조가 담당한다.

사용법:
  python3 .claude/scripts/consistency_check.py [docs_dir] [--strict] [--report]
    --strict : ❌ 오류가 있으면 종료코드 2 (Phase 게이트/대규모 변경 후 검증용)
    --report : 프로젝트별 prd/_consistency_report.md 저장

종료코드: 0=통과(또는 advisory), 2=--strict + 오류 있음
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_traceability import read, extract_refs

PRIORITY_RE = re.compile(r"\b(MUST|SHOULD|NICE|폐기)\b")
STAGE_RE = re.compile(r"\bP\d(?:-\d)?\b")
FS_ID_RE = re.compile(r"^FS-\d+$")
REQ_ID_RE = re.compile(r"^REQ-\d+$")


def cells_of(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    return [c.strip() for c in s.strip("|").split("|")]


def parse_prd_registry(prd_text):
    """ PRD 레지스트리: REQ → (우선순위, 단계). 추적표 행의 UNKNOWN 덮어쓰기 방지. """
    reg = {}
    for line in prd_text.splitlines():
        cells = cells_of(line)
        if not cells or not REQ_ID_RE.fullmatch(cells[0].replace("**", "")):
            continue
        rid = cells[0].replace("**", "")
        joined = " | ".join(cells[1:])
        pr = PRIORITY_RE.search(joined)
        st = STAGE_RE.search(joined)
        old_pr, old_st = reg.get(rid, (None, None))
        reg[rid] = (old_pr or (pr.group(1) if pr else None),
                    old_st or (st.group(0) if st else None))
    return reg


def parse_fs_rows(fs_text):
    """ 기능명세서 표: FS → (우선순위, 단계, 근거 REQ들, 중복 여부) """
    rows, dup = {}, set()
    for line in fs_text.splitlines():
        cells = cells_of(line)
        if not cells or not FS_ID_RE.fullmatch(cells[0].replace("**", "")):
            continue
        fid = cells[0].replace("**", "")
        # 우선·단계 칸: "SHOULD·P3-2" 형태가 있는 셀을 찾는다
        pr = st = None
        for c in cells[1:]:
            if PRIORITY_RE.search(c) and STAGE_RE.search(c):
                pr = PRIORITY_RE.search(c).group(1)
                st = STAGE_RE.search(c).group(0)
                break
        # 근거 REQ: 마지막 칸(연결)에서 우선 추출, 없으면 행 전체
        reqs = extract_refs(cells[-1])["REQ"] or extract_refs(" ".join(cells))["REQ"]
        if fid in rows:
            dup.add(fid)
        else:
            rows[fid] = (pr, st, reqs)
    return rows, dup


def check_project(proj_dir):
    prd_text = "\n".join(read(p) for p in sorted((proj_dir / "prd").glob("*.md"))
                         if not p.name.startswith("_") and p.name != "CHANGELOG.md")
    if not prd_text.strip():
        return None

    fs_text = "\n".join(read(p) for p in sorted((proj_dir / "fnspec").glob("*.md")))
    wbs_text = "\n".join(read(p) for p in sorted((proj_dir / "wbs").glob("*.md")))
    spec_text = read(proj_dir / "ui" / "03_screen_spec.md")
    ui_text = "\n".join(read(p) for p in sorted((proj_dir / "ui").glob("*.md")))

    lines, errors, warns = [], 0, 0

    def ok(t): lines.append(f"  ✅ {t}")
    def warn(t):
        nonlocal warns; warns += 1; lines.append(f"  ⚠️  {t}")
    def err(t):
        nonlocal errors; errors += 1; lines.append(f"  ❌ {t}")
    def head(t): lines.append(f"\n■ {t}")
    def fmt(ids): return ", ".join(sorted(ids))

    registry = parse_prd_registry(prd_text)

    # --- 1. 중복 선언 ---
    head("ID 중복 선언")
    fs_rows, fs_dup = parse_fs_rows(fs_text) if fs_text.strip() else ({}, set())
    if fs_dup:
        err(f"기능명세서에 두 번 선언된 FS: {fmt(fs_dup)}")
    else:
        ok("중복 선언 없음")

    # --- 2. FS 우선순위 상속 / 단계 일치 (fnspec 존재 시) ---
    if fs_rows:
        head("FS 우선순위 상속 (근거 REQ에서 상속, 임의 조정 금지)")
        bad_pr, bad_st, no_req = [], [], []
        for fid, (pr, st, reqs) in fs_rows.items():
            known = [r for r in reqs if r in registry]
            if not known:
                no_req.append(fid)
                continue
            req_prs = {registry[r][0] for r in known if registry[r][0]}
            req_sts = {registry[r][1] for r in known if registry[r][1]}
            if pr and req_prs and pr not in req_prs:
                bad_pr.append(f"{fid}({pr}≠{'/'.join(sorted(req_prs))})")
            if st and req_sts and st not in req_sts:
                bad_st.append(f"{fid}({st}≠{'/'.join(sorted(req_sts))})")
        if bad_pr:
            err(f"근거 REQ와 우선순위가 다른 FS: {', '.join(sorted(bad_pr))}")
        else:
            ok(f"FS {len(fs_rows)}행 전수 — 우선순위 상속 일치")
        if bad_st:
            warn(f"근거 REQ와 추진 단계가 다른 FS: {', '.join(sorted(bad_st))}")
        if no_req:
            warn(f"레지스트리에 있는 근거 REQ를 찾지 못한 FS: {fmt(no_req)}")

        # --- 3. MUST FS의 WBS 배치 ---
        if wbs_text.strip():
            head("MUST FS의 WBS 배치")
            must_fs = {f for f, (pr, _, _) in fs_rows.items() if pr == "MUST"}
            missing = {f for f in must_fs if f not in wbs_text}
            if missing:
                err(f"WBS에 배치되지 않은 MUST FS: {fmt(missing)}")
            else:
                ok(f"MUST FS {len(must_fs)}건 전부 WBS에 배치됨")

    # --- 4. 화면(SC) 산출물 커버리지 ---
    if spec_text.strip():
        head("화면(SC) 산출물 커버리지")
        declared_sc = {m.group(0).strip("()") for m in re.finditer(r"\(SC-\d+\)", spec_text)}
        wf_names = " ".join(p.name.lower() for p in (proj_dir / "assets" / "wireframes").glob("*.html"))
        scr_names = " ".join(p.name.lower() for p in (proj_dir / "ui" / "screens").glob("*.html"))
        no_wf = {s for s in declared_sc if f"sc-{s.split('-')[1]}" not in wf_names}
        no_scr = {s for s in declared_sc if f"sc-{s.split('-')[1]}" not in scr_names}
        if no_wf:
            warn(f"와이어프레임 파일이 없는 화면: {fmt(no_wf)}")
        if no_scr:
            warn(f"본 HTML 파일이 없는 화면: {fmt(no_scr)}")
        if not no_wf and not no_scr:
            ok(f"화면 {len(declared_sc)}개 전부 와이어프레임·본 HTML 존재")

    # --- 4b. 화면 HTML 상호 링크(cross-link) 유효성 ---
    #   본 HTML이 SC-ID로 명세·주석도해와 1:1 연결되는지 검사한다.
    #   AI·스크립트가 화면 하나만 열어도 나머지를 따라갈 수 있게 하는 규칙(스킬 11).
    screens_dir = proj_dir / "ui" / "screens"
    html_files = sorted(screens_dir.glob("*.html")) if screens_dir.is_dir() else []
    if html_files:
        head("화면 HTML 상호 링크")
        wf_files = {p.name for p in (proj_dir / "assets" / "wireframes").glob("*.html")}
        no_spec, bad_annot = [], []
        for html in html_files:
            t = read(html)
            if "03_screen_spec.md" not in t:
                no_spec.append(html.name)
            for m in re.finditer(r"annotated-[^\s\"'<>()]+\.html", t):
                ref = m.group(0).rsplit("/", 1)[-1]
                if ref not in wf_files:
                    bad_annot.append(f"{html.name}→{ref}")
        if no_spec:
            warn(f"명세 링크(03_screen_spec.md) 없는 화면 HTML: {fmt(set(no_spec))}")
        if bad_annot:
            warn(f"실재하지 않는 주석도해를 가리키는 화면 HTML: {', '.join(sorted(set(bad_annot)))}")
        if not no_spec and not bad_annot:
            ok(f"화면 HTML {len(html_files)}개 상호 링크 정상")

    # --- 5. 폐기 REQ의 활성 참조 ---
    retired = {r for r, (pr, _) in registry.items() if pr == "폐기"}
    if retired:
        head("폐기 REQ의 활성 참조")
        active = extract_refs(ui_text)["REQ"] | (extract_refs(fs_text)["REQ"] if fs_text else set())
        zombie = retired & active
        if zombie:
            err(f"폐기됐는데 활성 문서(UI·FS)가 참조 중인 REQ: {fmt(zombie)}")
        else:
            ok("폐기 REQ의 활성 참조 없음")

    return lines, errors, warns


def main():
    argv = sys.argv[1:]
    strict = "--strict" in argv
    write_report = "--report" in argv
    positional = [a for a in argv if not a.startswith("--")]
    docs_dir = Path(positional[0]) if positional else Path("docs")

    if not docs_dir.is_dir():
        print("ℹ️  docs/ 폴더가 없어 정합성 검사를 건너뜁니다.")
        return 0

    total_err = total_warn = 0
    out = ["═" * 50, "  내용 정합성 자동 검증 (기계 판정 항목)", "═" * 50]
    for proj in sorted(docs_dir.iterdir()):
        if not proj.is_dir() or proj.name.startswith("."):
            continue
        res = check_project(proj)
        if res is None:
            continue
        lines, errors, warns = res
        out.append(f"\n🗂  [{proj.name}]")
        out.extend(lines)
        status = "❌ 오류 있음" if errors else ("⚠️  경고 있음" if warns else "✅ 통과")
        out.append(f"  └─ 결과: {status} (오류 {errors} · 경고 {warns})")
        total_err += errors
        total_warn += warns

        if write_report:
            rpt = proj / "prd" / "_consistency_report.md"
            if rpt.parent.is_dir():
                block = "\n".join(lines).lstrip("\n")
                rpt.write_text(f"# 내용 정합성 검증 리포트 (기계 판정)\n\n"
                               f"- 대상: {proj.name}\n- 결과: 오류 {errors} · 경고 {warns}\n"
                               f"- 의미 대조(문장 충돌)는 별도: 스킬 15 참조\n\n"
                               f"```\n{block}\n```\n", encoding="utf-8")

    out.append("\n" + "─" * 50)
    out.append(f"총계: 오류 {total_err} · 경고 {total_warn}")
    out.append("ℹ️  문장 의미 충돌(수치·조건 불일치 등)은 기계 판정 불가 — 스킬 15(내용 정합성 검증)로 별도 수행")
    print("\n".join(out))
    return 2 if (strict and total_err) else 0


if __name__ == "__main__":
    sys.exit(main())
