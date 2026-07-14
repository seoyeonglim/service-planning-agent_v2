#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
검증기 회귀 테스트 (의존성 없음 — stdlib만).

목적: validate_traceability.py / consistency_check.py 의 로직을 고칠 때
      "고의로 깨진 문서를 넣으면 검증기가 잡는가 / 정상 문서는 통과시키는가"를
      자동으로 확인하는 안전망.

동작: 각 케이스마다 임시 docs 디렉터리에 소형 프로젝트를 만들고,
      해당 검증기를 --strict로 돌려 (종료코드 + 출력 문구)를 검사한다.
      임시 디렉터리는 실행 후 정리하므로 저장소를 건드리지 않는다.

실행: python3 tests/run_tests.py   (전체 통과 시 종료코드 0, 실패 시 1)
"""
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / ".claude/scripts/validate_traceability.py"
CONSIST = ROOT / ".claude/scripts/consistency_check.py"

# ── 픽스처 조각 ────────────────────────────────────────────────
REG = lambda rows: "## 요구사항 레지스트리\n| ID | 설명 | 우선순위 |\n|---|---|---|\n" + rows + "\n"
REG_ST = lambda rows: "## 요구사항 레지스트리\n| ID | 설명 | 우선순위 | 단계 |\n|---|---|---|---|\n" + rows + "\n"

PRD_GOOD = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |\n| REQ-002 | 알림 | SHOULD |") + \
           "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n\n### TC-002 (REQ-002)\n검증\n"

PRD_DANGLING = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |") + \
               "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n\n## 본문\n이 기능은 REQ-999 와 연계된다.\n"

PRD_MUST_NO_TC = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |\n| REQ-002 | 결제 | MUST |") + \
                 "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"

PRD_FS = "# PRD\n" + REG_ST("| REQ-001 | 로그인 | MUST | P1 |") + \
         "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"
FNSPEC_BADPRIO = "## 기능명세서\n| FS | 설명 | 우선·단계 | 근거 |\n|---|---|---|---|\n" + \
                 "| FS-001 | 로그인 처리 | SHOULD·P1 | REQ-001 |\n"

PRD_SCREEN = "# PRD\n" + REG("| REQ-001 | 랜딩 | MUST |") + \
             "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"
SPEC_SCREEN = "## 화면 명세서\n### 화면명: 랜딩 (SC-01)\n- **관련 REQ:** REQ-001\n- **우선순위:** MUST\n"
HTML_NOLINK = "<!DOCTYPE html>\n<!-- SC-01 | 랜딩 | REQ-001 | TC-001 -->\n<html><body>랜딩</body></html>\n"

# 별도 칸 우선순위(버그 회귀): 우선순위가 단계와 다른 칸/단독 칸에 있어도 잡아야 함
FNSPEC_SEP_BADPRIO = "## 기능명세서\n| FS-ID | 기능명 | 설명 | 예외 | 우선·단계 | 연결 |\n|---|---|---|---|---|---|\n" + \
                     "| FS-001 | 로그인 | 처리 | - | NICE | REQ-001 |\n"
# MUST FS가 WBS에 미배치
FNSPEC_MUST = "## 기능명세서\n| FS-ID | 기능명 | 설명 | 우선·단계 | 연결 |\n|---|---|---|---|---|\n" + \
              "| FS-001 | 로그인 | 처리 | MUST·P1 | REQ-001 |\n"
WBS_NOFS = "## WBS\n- 주차1: 환경 구성\n- 주차2: 배포\n"
# 폐기 REQ를 활성 문서(UI)가 참조
PRD_RETIRED = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |\n| REQ-002 | 구기능 | 폐기 |") + \
              "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"
UI_ZOMBIE = "## 정보구조\n랜딩은 REQ-002 를 계속 노출한다.\n"
# PRD 레지스트리에 같은 REQ가 서로 다른 우선순위로 중복 선언 (PRD 내부 정합성)
PRD_REQ_DUP = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |\n| REQ-001 | 로그인(중복) | SHOULD |") + \
              "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"

# ── 검증기 자체 결함 회귀 픽스처 (2026-07 사냥 결과 8건) ──────────
# (1) 볼드 REQ: **REQ-###** 표기도 선언으로 인식해야 함 (REQ-002는 TC 없는 MUST)
PRD_BOLD = "# PRD\n" + REG("| **REQ-001** | 로그인 | MUST |\n| **REQ-002** | 결제 | MUST |") + \
           "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"
# (4) TC가 0개인 PRD: 'TC 없는 MUST' 검사가 성립 불가 → 통과가 아니라 차단이어야 함
PRD_ZERO_TC = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |")
# (6) 스코프 제외 표의 REQ 행이 '선언'으로 오염되면 안 됨 (REQ-050은 레지스트리에 없음)
PRD_SCOPE_OUT = "# PRD\n## 제외 범위\n| ID | 사유 |\n|---|---|\n| REQ-050 | 다음 버전 |\n" + \
                REG("| REQ-001 | 로그인 | MUST |") + \
                "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n### TC-050 (REQ-050)\n검증\n"
# (7) 범위 참조(REQ-001~005)의 의도적 결번(002·004)은 ❌가 아니라 ⚠️여야 함
PRD_RANGE = "# PRD\n" + REG("| REQ-001 | A | MUST |\n| REQ-003 | B | MUST |\n| REQ-005 | C | MUST |") + \
            "## 개요\n본 서비스는 REQ-001~005 기능군으로 구성된다.\n" + \
            "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n### TC-003 (REQ-003)\n검증\n### TC-005 (REQ-005)\n검증\n"
# (8) CHANGELOG의 과거 ID 인용이 유령 참조로 오탐되면 안 됨
CHANGELOG_OLD = "# 변경 기록\n## CR-001\n- 대상: REQ-777 (폐기된 과거 임시 ID)\n"
# (5) 우선순위 미인식('필수' 등) FS는 조용히 빠지지 말고 경고로 표면화
FNSPEC_KR_PRIO = "## 기능명세서\n| FS-ID | 기능명 | 우선·단계 | 연결 |\n|---|---|---|---|\n" + \
                 "| FS-001 | 로그인 | 필수·P1 | REQ-001 |\n"
# (3) FS-01이 WBS의 FS-010에 부분문자열로 매칭돼 '배치됨' 오판하면 안 됨
FNSPEC_MUST_SHORT = "## 기능명세서\n| FS-ID | 기능명 | 우선·단계 | 연결 |\n|---|---|---|---|\n" + \
                    "| FS-01 | 로그인 | MUST·P1 | REQ-001 |\n"
WBS_SIMILAR = "## WBS\n- 주차1: FS-010 관련 작업\n"
# (2) SC-01 산출물이 없는데 sc-010 파일이 있으면 '존재'로 오판하면 안 됨
SPEC_SC01 = "## 화면 명세서\n### 화면명: 랜딩 (SC-01)\n- **관련 REQ:** REQ-001\n"
HTML_OTHER = "<!DOCTYPE html>\n<!-- SC-010 | 기타 | REQ-001 -->\n<html><body>03_screen_spec.md</body></html>\n"

# ── 우선순위 어휘 '제외'(범위 밖 이관) — 폐기와 구분되는 5번째 상태 ──────────
# 제외 REQ: TC 없어도 되고, 활성 문서가 참조해도 오류 아님(범위 경계 기록 — 폐기와 다름)
PRD_EXCLUDED = "# PRD\n" + REG("| REQ-001 | 로그인 | MUST |\n| REQ-090 | OCR 업로드 | **제외** |\n| REQ-091 | 어시스턴트 탭 | 제외(2차) |") + \
               "## 테스트 케이스\n### TC-001 (REQ-001)\n검증\n"
UI_REF_EXCLUDED = "## 정보구조\n랜딩은 REQ-001 기준. REQ-090 은 확장 로드맵으로 이관되어 본 사업 미구현.\n"
# 설명 속 일반 단어 '제외'는 우선순위가 아님 — 영문 토큰(MUST)이 이겨야 함
PRD_KR_IN_DESC = "# PRD\n" + REG("| REQ-001 | 로그인(게스트 제외) | MUST |") + "\n"

# ── 케이스 정의 ────────────────────────────────────────────────
# exit: 기대 종료코드 / contains: 출력에 있어야 할 문구 / absent: 없어야 할 문구
CASES = [
    dict(name="정상 PRD → 추적성 통과", checker=TRACE, exit=0,
         files={"prd/PRD.md": PRD_GOOD}, absent=["❌"]),
    dict(name="정상 PRD → 정합성 통과", checker=CONSIST, exit=0,
         files={"prd/PRD.md": PRD_GOOD}, absent=["❌"]),
    dict(name="유령 REQ 참조 → 추적성 ❌ 검출", checker=TRACE, exit=2,
         files={"prd/PRD.md": PRD_DANGLING}, contains=["유령 참조", "REQ-999"]),
    dict(name="TC 없는 MUST REQ → 추적성 ❌ 검출", checker=TRACE, exit=2,
         files={"prd/PRD.md": PRD_MUST_NO_TC}, contains=["없는 MUST REQ", "REQ-002"]),
    dict(name="FS 우선순위 상속 불일치 → 정합성 ❌ 검출", checker=CONSIST, exit=2,
         files={"prd/PRD.md": PRD_FS, "fnspec/기능명세서.md": FNSPEC_BADPRIO},
         contains=["우선순위가 다른 FS", "FS-001"]),
    dict(name="화면 상호 링크 누락 → 정합성 ⚠️ 검출", checker=CONSIST, exit=0,
         files={"prd/PRD.md": PRD_SCREEN, "ui/03_screen_spec.md": SPEC_SCREEN,
                "ui/screens/sc-01.html": HTML_NOLINK},
         contains=["명세 링크(03_screen_spec.md) 없는 화면 HTML"]),
    dict(name="별도 칸 FS 우선순위 불일치 → 정합성 ❌ 검출 (버그 회귀 방지)", checker=CONSIST, exit=2,
         files={"prd/PRD.md": PRD_FS, "fnspec/기능명세서.md": FNSPEC_SEP_BADPRIO},
         contains=["우선순위가 다른 FS", "FS-001"]),
    dict(name="MUST FS가 WBS에 미배치 → 정합성 ❌ 검출", checker=CONSIST, exit=2,
         files={"prd/PRD.md": PRD_FS, "fnspec/기능명세서.md": FNSPEC_MUST, "wbs/WBS.md": WBS_NOFS},
         contains=["WBS에 배치되지 않은 MUST FS", "FS-001"]),
    dict(name="폐기 REQ를 활성 문서가 참조 → 정합성 ❌ 검출", checker=CONSIST, exit=2,
         files={"prd/PRD.md": PRD_RETIRED, "ui/01_information_architecture.md": UI_ZOMBIE},
         contains=["폐기됐는데 활성 문서", "REQ-002"]),
    dict(name="레지스트리 REQ 중복·우선순위 상충 → 정합성 ⚠️ 검출 (PRD 내부)", checker=CONSIST, exit=0,
         files={"prd/PRD.md": PRD_REQ_DUP},
         contains=["우선순위가 상충하는 REQ", "REQ-001"]),
    # ── 검증기 자체 결함 회귀 (2026-07 사냥 결과 8건) ──────────
    dict(name="[결함1] 볼드 REQ 선언 인식 → TC 없는 MUST ❌ 검출", checker=TRACE, exit=2,
         files={"prd/PRD.md": PRD_BOLD},
         contains=["없는 MUST REQ", "REQ-002"], absent=["유령 참조"]),
    dict(name="[결함2] SC-01 산출물 부재 + sc-010만 존재 → ⚠️ 검출(부분문자열 오판 금지)", checker=CONSIST, exit=0,
         files={"prd/PRD.md": PRD_GOOD, "ui/03_screen_spec.md": SPEC_SC01,
                "ui/screens/sc-010-other.html": HTML_OTHER,
                "assets/wireframes/wf-sc-010-other.html": HTML_OTHER},
         contains=["와이어프레임 파일이 없는 화면", "SC-01"]),
    dict(name="[결함3] MUST FS-01 미배치 + WBS에 FS-010만 → ❌ 검출(부분문자열 오판 금지)", checker=CONSIST, exit=2,
         files={"prd/PRD.md": PRD_FS, "fnspec/기능명세서.md": FNSPEC_MUST_SHORT,
                "wbs/WBS.md": WBS_SIMILAR},
         contains=["WBS에 배치되지 않은 MUST FS", "FS-01"]),
    dict(name="[결함4] TC 0개 + MUST 존재 → 추적성 ❌ 차단(경고 강등 금지)", checker=TRACE, exit=2,
         files={"prd/PRD.md": PRD_ZERO_TC},
         contains=["하나도 없음", "미검증"]),
    dict(name="[결함5] 우선순위 미인식 FS('필수') → ⚠️ 표면화(조용한 게이트 회피 금지)", checker=CONSIST, exit=0,
         files={"prd/PRD.md": PRD_FS, "fnspec/기능명세서.md": FNSPEC_KR_PRIO},
         contains=["우선순위(MUST/SHOULD/NICE/폐기/제외)를 인식하지 못한 FS", "FS-001"]),
    dict(name="[결함6] 스코프 제외 표 REQ는 선언 아님 → 유령 참조 ❌ 검출", checker=TRACE, exit=2,
         files={"prd/PRD.md": PRD_SCOPE_OUT},
         contains=["유령 참조", "REQ-050"]),
    dict(name="[결함7] 범위 참조 결번(REQ-001~005의 002·004) → ⚠️만, ❌ 오탐 금지", checker=TRACE, exit=0,
         files={"prd/PRD.md": PRD_RANGE},
         contains=["범위 참조", "REQ-002"], absent=["유령 참조"]),
    dict(name="[결함8] CHANGELOG의 과거 ID 인용 → 유령 참조 오탐 금지", checker=TRACE, exit=0,
         files={"prd/PRD.md": PRD_GOOD, "prd/CHANGELOG.md": CHANGELOG_OLD},
         absent=["REQ-777", "❌"]),
    # ── 우선순위 어휘 '제외' (범위 밖 이관 상태) ──────────
    dict(name="[제외] 제외 REQ는 TC 불요·미인식 경고 없음 → 추적성 통과", checker=TRACE, exit=0,
         files={"prd/PRD.md": PRD_EXCLUDED},
         absent=["❌", "인식하지 못한 REQ"]),
    dict(name="[제외] 제외 REQ를 활성 문서가 참조 → 좀비 아님(폐기와 구분)", checker=CONSIST, exit=0,
         files={"prd/PRD.md": PRD_EXCLUDED, "ui/01_information_architecture.md": UI_REF_EXCLUDED},
         absent=["❌"]),
    dict(name="[제외] 설명 속 '제외'보다 영문 MUST 우선 → TC 없는 MUST ❌ 검출", checker=TRACE, exit=2,
         files={"prd/PRD.md": PRD_KR_IN_DESC},
         contains=["MUST REQ 1건 미검증"]),
]


def run_case(c):
    tmp = Path(tempfile.mkdtemp(prefix="vtest_"))
    try:
        for rel, content in c["files"].items():
            f = tmp / "proj" / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")
        r = subprocess.run([sys.executable, str(c["checker"]), str(tmp), "--strict"],
                           capture_output=True, text=True)
        fails = []
        if r.returncode != c["exit"]:
            fails.append(f"종료코드 {r.returncode}≠기대 {c['exit']}")
        for sub in c.get("contains", []):
            if sub not in r.stdout:
                fails.append(f"출력에 '{sub}' 없음")
        for sub in c.get("absent", []):
            if sub in r.stdout:
                fails.append(f"출력에 '{sub}' 있으면 안 됨")
        return fails, r.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("═" * 56)
    print("  검증기 회귀 테스트")
    print("═" * 56)
    n_fail = 0
    for c in CASES:
        fails, out = run_case(c)
        if fails:
            n_fail += 1
            print(f"  ❌ {c['name']}")
            for f in fails:
                print(f"       - {f}")
        else:
            print(f"  ✅ {c['name']}")
    print("─" * 56)
    if n_fail:
        print(f"실패 {n_fail}/{len(CASES)} — 검증기 로직 회귀 의심")
        return 1
    print(f"전체 통과 {len(CASES)}/{len(CASES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
