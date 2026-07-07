#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.claude/skills  →  .codex/skills 동기화 스크립트 (서비스 기획 에이전트)

하는 일 (쉽게):
  번호 스킬(01~11)의 원본은 `.claude/skills/NN_name.md` 하나뿐이다.
  Codex CLI는 `.codex/skills/NN-name/SKILL.md`(프론트매터 포함)를 읽는데,
  지금까지는 이 복제본을 손으로 맞춰야 했다. 이 스크립트가 원본에서 자동 생성한다.

변환 규칙:
  - 파일명  06_test_cases.md      → 디렉터리 06-test-cases/SKILL.md
  - name    "06-test-cases"       (밑줄 → 하이픈)
  - description "Project planning workflow skill: <첫 H1 텍스트>."
  - 본문    .claude 원본을 그대로 복사 (경로/참조 재작성 없음)

예외:
  - visual_generation 은 프론트매터가 수작업 커스텀(disable-model-invocation 등)이라
    자동 동기화 대상에서 제외한다. (손으로 관리)

사용법:
  python3 .claude/scripts/sync_codex_skills.py          # 변경분 반영(쓰기)
  python3 .claude/scripts/sync_codex_skills.py --check   # 쓰지 않고 드리프트만 점검(다르면 종료코드 2)
  python3 .claude/scripts/sync_codex_skills.py --prune    # 원본이 없어진 .codex 번호 스킬 디렉터리 삭제

종료코드: 0=동기화됨/일치, 2=--check에서 드리프트 발견
"""

import re
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # 프로젝트 루트
CLAUDE_SKILLS = ROOT / ".claude" / "skills"
CODEX_SKILLS = ROOT / ".codex" / "skills"

EXCLUDE = {"visual_generation"}              # 수작업 관리 — 건드리지 않음
SKILL_RE = re.compile(r"^\d{2}_[a-z0-9_]+\.md$")
H1_RE = re.compile(r"^#\s+(.*?)\s*$", re.M)


def kebab(stem):
    """ 06_test_cases → 06-test-cases """
    return stem.replace("_", "-")


def build_codex_content(src_text):
    m = H1_RE.search(src_text)
    h1 = m.group(1) if m else "Project planning workflow skill"
    name = None  # 호출부에서 채움
    return h1, src_text


def expected_for(src_path):
    """ 원본 .md → (대상 SKILL.md 경로, 기대 내용) """
    stem = src_path.stem                       # 06_test_cases
    dir_name = kebab(stem)                     # 06-test-cases
    target = CODEX_SKILLS / dir_name / "SKILL.md"
    body = src_path.read_text(encoding="utf-8")
    m = H1_RE.search(body)
    h1 = m.group(1) if m else stem
    front = (
        "---\n"
        f'name: "{dir_name}"\n'
        f'description: "Project planning workflow skill: {h1}."\n'
        "---\n"
        "\n"
    )
    return target, front + body


def main():
    argv = sys.argv[1:]
    check = "--check" in argv
    prune = "--prune" in argv
    quiet = "--quiet" in argv   # 변경/고아가 없으면 아무 것도 출력하지 않음(훅용)

    if not CLAUDE_SKILLS.is_dir():
        print(f"❌ 원본 폴더 없음: {CLAUDE_SKILLS}")
        return 2

    sources = sorted(p for p in CLAUDE_SKILLS.iterdir()
                     if p.is_file() and SKILL_RE.match(p.name))

    created, updated, unchanged = [], [], []
    for src in sources:
        target, content = expected_for(src)
        if target.exists() and target.read_text(encoding="utf-8") == content:
            unchanged.append(target)
            continue
        existed = target.exists()
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (updated if existed else created).append(target)

    # 원본이 사라진 .codex 번호 스킬 디렉터리 탐지
    valid_dirs = {kebab(p.stem) for p in sources} | EXCLUDE
    orphans = [d for d in CODEX_SKILLS.iterdir()
               if d.is_dir() and re.match(r"^\d{2}-", d.name) and d.name not in valid_dirs]

    # 조용 모드: 바뀐 것도 고아도 없으면 침묵
    if quiet and not (created or updated or orphans):
        return 0

    # 리포트
    print("═" * 46)
    print("  .claude/skills → .codex/skills 동기화")
    print("═" * 46)
    print(f"원본 스킬: {len(sources)}개 · 제외(수작업): {', '.join(sorted(EXCLUDE))}")
    verb = "변경 필요" if check else "반영됨"
    for t in created:
        print(f"  🆕 생성{'(예정)' if check else ''}: {t.relative_to(ROOT)}")
    for t in updated:
        print(f"  ✏️  {verb}: {t.relative_to(ROOT)}")
    if not created and not updated:
        print(f"  ✅ 모든 번호 스킬이 이미 일치 ({len(unchanged)}개)")
    else:
        print(f"  (일치 {len(unchanged)}개)")

    for d in orphans:
        if prune and not check:
            shutil.rmtree(d)
            print(f"  🗑  고아 삭제: {d.relative_to(ROOT)}")
        else:
            print(f"  ⚠️  고아(원본 없음): {d.relative_to(ROOT)}  → --prune 으로 삭제 가능")

    drift = bool(created or updated)
    print("─" * 46)
    if check:
        print("드리프트 있음 ❌" if drift else "동기화 상태 양호 ✅")
        return 2 if drift else 0
    print(f"완료: 생성 {len(created)} · 갱신 {len(updated)} · 유지 {len(unchanged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
