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
  - 화면 인덱스(ui/screens/index.html, 자동 생성)가 존재하고 전 화면을 수록하나
  - 폐기된 REQ가 활성 문서에서 여전히 참조되나
  - 같은 FS ID가 두 번 선언되지 않았나
  - PRD 레지스트리에 같은 REQ가 중복 선언·우선순위 상충하지 않았나 (PRD 내부 정합성)

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
from validate_traceability import read, extract_refs, registry_sections, find_priority

STAGE_RE = re.compile(r"\bP\d(?:-\d)?\b")
FS_ID_RE = re.compile(r"^FS-\d+$")
REQ_ID_RE = re.compile(r"^REQ-\d+$")


def id_in_text(fid, text):
    """ ID가 텍스트에 '정확히' 등장하는가 — FS-01이 FS-010에 부분문자열로
    걸리는 오탐(누락을 배치됨으로 오판)을 막기 위해 숫자 경계를 강제한다. """
    return re.search(rf"\b{re.escape(fid)}(?!\d)", text) is not None


def sc_numbers(names_text):
    """ 파일명 문자열에서 화면 번호(sc-N)를 숫자 집합으로 추출.
    부분문자열 비교(sc-01 ⊂ sc-010) 대신 숫자 동등 비교를 하기 위함. """
    return {int(m.group(1)) for m in re.finditer(r"sc-(\d+)", names_text)}


def cells_of(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    return [c.strip() for c in s.strip("|").split("|")]


def parse_prd_registry(prd_text):
    """ PRD 레지스트리: REQ → (우선순위, 단계). 추적표 행의 UNKNOWN 덮어쓰기 방지.
    '요구사항 레지스트리' 섹션만 읽는다 — 전체를 훑으면 스코프 제외 표 등
    다른 표의 REQ 행이 선언·우선순위로 오염된다. (헤딩 없으면 전체로 폴백) """
    reg = {}
    source = registry_sections(prd_text) or prd_text
    for line in source.splitlines():
        cells = cells_of(line)
        if not cells or not REQ_ID_RE.fullmatch(cells[0].replace("**", "")):
            continue
        rid = cells[0].replace("**", "")
        # V와 동일한 판정 함수 공유 — 두 검증기가 같은 문서를 다르게 읽지 않게 한다
        pr = find_priority(cells[1:])
        pr = None if pr == "UNKNOWN" else pr
        st = STAGE_RE.search(" | ".join(cells[1:]))
        old_pr, old_st = reg.get(rid, (None, None))
        reg[rid] = (old_pr or pr, old_st or (st.group(0) if st else None))
    return reg


def parse_fs_rows(fs_text):
    """ 기능명세서 표: FS → (우선순위, 단계, 근거 REQ들) + 중복 ID + 우선순위 미인식 ID """
    rows, dup, no_prio = {}, set(), set()
    for line in fs_text.splitlines():
        cells = cells_of(line)
        if not cells or not FS_ID_RE.fullmatch(cells[0].replace("**", "")):
            continue
        fid = cells[0].replace("**", "")
        # 우선순위·단계: 한 셀에 같이 있든("SHOULD·P3-2") 별도 칸으로 나뉘든 모두 인식.
        # (한 셀 결합만 인식하면, 우선순위 단독 칸 템플릿으로 쓴 표에서 ②우선순위 상속·
        #  ④MUST FS WBS 배치 검사가 조용히 no-op가 된다.)
        pr = find_priority(cells[1:])
        pr = None if pr == "UNKNOWN" else pr
        st = None
        for c in cells[1:]:
            sm = STAGE_RE.search(c)
            if sm and st is None:
                st = sm.group(0)
        if pr is None:
            # 우선순위를 못 읽으면 그 FS는 MUST 검사(상속·WBS 배치)에서 통째로
            # 빠진다(조용한 게이트 회피) — 반드시 표면화한다.
            no_prio.add(fid)
        # 근거 REQ: 마지막 칸(연결)에서 우선 추출, 없으면 행 전체
        reqs = extract_refs(cells[-1])["REQ"] or extract_refs(" ".join(cells))["REQ"]
        if fid in rows:
            dup.add(fid)
        else:
            rows[fid] = (pr, st, reqs)
    return rows, dup, no_prio


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
    fs_rows, fs_dup, fs_no_prio = (parse_fs_rows(fs_text) if fs_text.strip()
                                   else ({}, set(), set()))
    if fs_dup:
        err(f"기능명세서에 두 번 선언된 FS: {fmt(fs_dup)}")
    else:
        ok("중복 선언 없음")
    if fs_no_prio:
        warn(f"우선순위(MUST/SHOULD/NICE/폐기/제외)를 인식하지 못한 FS — "
             f"상속·WBS 배치 검사에서 빠짐: {fmt(fs_no_prio)}")

    # --- 1b. PRD 레지스트리 REQ 중복/우선순위 상충 (C: PRD 내부 정합성) ---
    #   '요구사항 레지스트리' 섹션 안의 REQ 행만 센다 (헤딩 레벨 무관 — 공용 헬퍼).
    #   전체 PRD를 훑으면 스코프 표·추적표 등 다른 표의 REQ까지 잡혀 오탐이 폭발한다.
    head("PRD 레지스트리 REQ 중복 선언")
    req_prio = {}
    for line in (registry_sections(prd_text) or "").splitlines():
        cells = cells_of(line)
        if not cells or not REQ_ID_RE.fullmatch(cells[0].replace("**", "")):
            continue
        pm = find_priority(cells[1:])
        if pm == "UNKNOWN":
            continue
        req_prio.setdefault(cells[0].replace("**", ""), []).append(pm)
    dup_req = {r for r, ps in req_prio.items() if len(ps) > 1}
    conflict_req = {r for r in dup_req if len(set(req_prio[r])) > 1}
    if conflict_req:
        warn("레지스트리에서 우선순위가 상충하는 REQ: "
             + ", ".join(f"{r}({'/'.join(req_prio[r])})" for r in sorted(conflict_req)))
    if dup_req - conflict_req:
        warn(f"레지스트리에 두 번 이상 정의된 REQ: {fmt(dup_req - conflict_req)}")
    if not dup_req:
        ok("REQ 중복 선언 없음")

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
            missing = {f for f in must_fs if not id_in_text(f, wbs_text)}
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
        # 숫자 동등 비교 — 부분문자열 비교는 sc-01⊂sc-010, sc-1⊂sc-15에 걸려
        # '산출물 없음'을 '있음'으로 오판한다
        wf_nums, scr_nums = sc_numbers(wf_names), sc_numbers(scr_names)
        no_wf = {s for s in declared_sc if int(s.split("-")[1]) not in wf_nums}
        no_scr = {s for s in declared_sc if int(s.split("-")[1]) not in scr_nums}
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
    # index.html은 자동 생성 인덱스(generate_screen_index.py) — 화면이 아니므로 제외
    html_files = sorted(p for p in screens_dir.glob("*.html")
                        if p.name != "index.html") if screens_dir.is_dir() else []
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

    # --- 4c. 화면 인덱스(index.html) 존재·신선도 ---
    #   개발자용 한눈 인덱스가 있고, 모든 화면 파일을 담고 있는지 본다.
    #   자동 생성물이라 재생성만 하면 되므로 경고(⚠️)로만 표면화한다.
    if html_files:
        head("화면 인덱스(자동 생성)")
        regen = "재생성: python3 .claude/scripts/generate_screen_index.py"
        index_path = screens_dir / "index.html"
        if not index_path.is_file():
            warn(f"화면 인덱스(ui/screens/index.html)가 없음 — {regen}")
        else:
            idx_text = read(index_path)
            stale = [p.name for p in html_files if p.name not in idx_text]
            if stale:
                warn(f"화면 인덱스에 없는 화면 HTML(인덱스가 낡음): {fmt(set(stale))} — {regen}")
            else:
                ok(f"화면 인덱스가 화면 {len(html_files)}개 전부 수록")

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
    ROOT = Path(__file__).resolve().parents[2]  # 워크플로우 루트 (CWD 무관)
    docs_dir = Path(positional[0]) if positional else ROOT / "docs"
    if not docs_dir.exists() and not docs_dir.is_absolute() and (ROOT / docs_dir).exists():
        docs_dir = ROOT / docs_dir  # 프로젝트 폴더 등에서 상대경로로 실행돼도 루트 기준으로 복원

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
