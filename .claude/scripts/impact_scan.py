#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변경 영향 범위 스캔 스크립트 (서비스 기획 에이전트)

하는 일 (쉽게):
  "REQ-041을 바꿀 건데, 어느 문서들을 같이 확인해야 하지?"에 답한다.
  지정한 ID(REQ/EC/TC/SC/FS)가 등장하는 모든 산출물 파일을 찾아
  체크리스트로 출력한다 — CR(변경 기록)의 `변경 범위` 칸 초안용.

  ⚠️ 이 스크립트는 "확인할 위치"만 알려준다. 내용이 서로 일치하는지는
  사람이(또는 게이트에서) 직접 대조해야 한다.

사용법:
  python3 .claude/scripts/impact_scan.py REQ-041                 # 전체 프로젝트에서 스캔
  python3 .claude/scripts/impact_scan.py REQ-041 EC-03 TC-018    # 여러 ID 동시 스캔
  python3 .claude/scripts/impact_scan.py REQ-041 --project kyobo_lifeplanet_ai_salesbot
  python3 .claude/scripts/impact_scan.py REQ-041 --md            # CR에 붙여넣을 마크다운 체크리스트로 출력

제외 폴더: _archive/(과거 버전), ref/(고객사 원자료) — 변경 대상이 아니므로 스캔하지 않음
제외 파일: _traceability_report.md·_consistency_report.md(자동 생성물)

종료코드: 0=정상, 1=해당 ID가 어디에도 없음(오타 가능성)
"""

import sys
import re
from pathlib import Path

# validate_traceability.py의 ID 인식 로직 재사용
#  - REQ-001~005(범위), REQ-070·071(나열), TC-020-01(복합) 표기를 모두 개별 ID로 펼쳐 인식
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_traceability import extract_refs, read

# FS-###도 스캔 대상에 포함 (기능명세서 단계에서 도입되는 ID)
FS_RE = re.compile(r"FS-\d+")

EXCLUDE_DIRS = {"_archive", "ref"}
EXCLUDE_FILES = {"_traceability_report.md", "_consistency_report.md"}
SCAN_SUFFIXES = {".md", ".html"}

ID_FORM = re.compile(r"^(REQ|EC|TC|SC|FS)-\d+(?:-\d+)?$")


def refs_in(text):
    """ 파일 하나에서 언급된 모든 ID를 집합으로 반환 (FS 포함) """
    refs = extract_refs(text)
    ids = set().union(*refs.values())
    ids |= {m.group(0) for m in FS_RE.finditer(text)}
    return ids


def scan_files(proj_dir):
    """ 프로젝트 폴더에서 스캔 대상 파일 목록을 뽑는다 """
    for path in sorted(proj_dir.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.name in EXCLUDE_FILES:
            continue
        rel_parts = path.relative_to(proj_dir).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        yield path


def count_lines(text, target_ids):
    """ 대상 ID가 등장하는 줄 번호 목록 (축약 표기 포함) """
    lines = []
    for i, line in enumerate(text.splitlines(), 1):
        if target_ids & refs_in(line):
            lines.append(i)
    return lines


def main():
    argv = sys.argv[1:]
    as_md = "--md" in argv
    project = None
    if "--project" in argv:
        idx = argv.index("--project")
        project = argv[idx + 1] if idx + 1 < len(argv) else None
        argv = argv[:idx] + argv[idx + 2:]
    targets = {a for a in argv if not a.startswith("--")}

    bad = {t for t in targets if not ID_FORM.match(t)}
    if not targets or bad:
        print(f"사용법: impact_scan.py <REQ-###|EC-##|TC-###|SC-##|FS-###>... [--project 이름] [--md]")
        if bad:
            print(f"  잘못된 ID 형식: {', '.join(sorted(bad))}")
        return 1

    docs_dir = Path("docs")
    if not docs_dir.is_dir():
        print("ℹ️  docs/ 폴더가 없습니다.")
        return 1

    projects = [d for d in sorted(docs_dir.iterdir()) if d.is_dir() and not d.name.startswith(".")]
    if project:
        projects = [d for d in projects if d.name == project]
        if not projects:
            print(f"❌ 프로젝트를 찾을 수 없음: {project}")
            return 1

    total_hits = 0
    for proj in projects:
        hits = []  # (상대경로, 등장 줄 번호들)
        for path in scan_files(proj):
            text = read(path)
            if not (targets & refs_in(text)):
                continue
            hits.append((path.relative_to(proj), count_lines(text, targets)))
        if not hits:
            continue
        total_hits += len(hits)

        if as_md:
            print(f"**변경 범위 초안** — 대상: {', '.join(sorted(targets))} ({proj.name})")
            for rel, lines in hits:
                print(f"- [ ] {rel} ({len(lines)}곳)")
        else:
            print(f"\n🗂  [{proj.name}] — 대상: {', '.join(sorted(targets))}")
            for rel, lines in hits:
                shown = ", ".join(f"L{n}" for n in lines[:8])
                more = f" 외 {len(lines) - 8}곳" if len(lines) > 8 else ""
                print(f"  □ {rel}  ({len(lines)}곳: {shown}{more})")
            print(f"  └─ 총 {len(hits)}개 파일 — 각 파일을 확인하고 CR의 `변경 범위` 칸에 결과를 기록하세요.")

    if total_hits == 0:
        print(f"⚠️  {', '.join(sorted(targets))} 를 언급하는 문서가 없습니다 — ID 오타이거나 아직 정의 전일 수 있습니다.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
