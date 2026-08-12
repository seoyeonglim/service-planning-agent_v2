#!/bin/bash
# ─────────────────────────────────────────────────────────────
# 커밋 게이트 (서비스 기획 에이전트)
#
# 프로젝트 저장소의 commit-msg 훅에서 호출된다. $1 = 커밋 메시지 파일 경로.
# 하는 일 (순서대로):
#   ① validate_traceability.py --strict  → ID 연결(추적성) 검사, ❌ 시 커밋 차단
#   ② consistency_check.py     --strict  → 내용 정합성(기계 판정) 검사, ❌ 시 차단
#   ③ 스킬 15(문장 의미 대조)             → `[handoff]` 마커가 있는 커밋일 때만 확인 토큰 요구
#   ④ check-design-tokens.mjs            → 화면 HTML 의 디자인 토큰 이탈 검사
#
# ①②는 기계가 자동으로 판정하고, ③은 에이전트가 수행하는 작업이라 훅이 대신
# 실행할 수 없다. 그래서 개발 핸드오프 커밋에서만 "수행했다"는 토큰을 요구한다.
# 일상 초안 커밋은 ①②만 통과하면 된다.
#
# ④는 ax-design-system 에서 vendoring 한 디자인 게이트다. **기본은 조언(advisory)
# 모드로 차단하지 않는다** — 도입 시점의 기존 화면 baseline 이 ERROR 수천 건이라
# 차단으로 켜면 기존 프로젝트의 커밋이 전부 막히기 때문(brownfield 무결성 RULE).
# 신규 프로젝트처럼 ERROR 0 을 유지할 수 있는 저장소는 아래 둘 중 하나로 차단을
# 켠다:
#   - 저장소 루트에 `.design-gate-strict` 파일을 만든다, 또는
#   - 환경변수 `DESIGN_GATE=strict` 로 커밋한다.
# ─────────────────────────────────────────────────────────────
set -u

MSG_FILE="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
PROJ_NAME="$(basename "$REPO_ROOT")"

# 기획 프로젝트 저장소가 아니면(= prd/ 폴더가 없으면) 조용히 통과.
# 전역 템플릿으로 설치돼 다른 코딩 저장소에도 붙더라도 방해하지 않기 위함.
if [ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT/prd" ]; then
  exit 0
fi

TRACE="$SCRIPT_DIR/validate_traceability.py"
CONSIST="$SCRIPT_DIR/consistency_check.py"

# 워크플로우 스크립트가 없으면(예: 개발 핸드오프 사본 레포) 조용히 통과
if [ ! -f "$TRACE" ] || [ ! -f "$CONSIST" ]; then
  echo "ℹ️  커밋 게이트: 워크플로우 스크립트를 찾을 수 없어 검사를 건너뜁니다."
  exit 0
fi

# 이 프로젝트 하나만 검사하도록 임시 docs/ 에 심링크로 스코프
# (스크립트는 docs_dir 하위의 각 폴더를 개별 프로젝트로 훑기 때문에,
#  형제 프로젝트의 오류로 이 커밋이 막히지 않게 격리한다.)
TMP="$(mktemp -d)"
ln -s "$REPO_ROOT" "$TMP/$PROJ_NAME"
cleanup() { rm -rf "$TMP"; }   # 심링크만 지움 — 실제 프로젝트는 건드리지 않음
trap cleanup EXIT

echo "═══════════ 커밋 게이트 ($PROJ_NAME) ═══════════"

echo ""
echo "▶ ① 요구사항 추적성 검사 (validate_traceability.py --strict)"
python3 "$TRACE" "$TMP" --strict
RC1=$?

echo ""
echo "▶ ② 내용 정합성 검사 (consistency_check.py --strict)"
python3 "$CONSIST" "$TMP" --strict
RC2=$?

if [ "$RC1" -ne 0 ] || [ "$RC2" -ne 0 ]; then
  echo ""
  echo "❌ 커밋 차단 — 위 ❌ 오류를 먼저 보완한 뒤 다시 커밋하세요. (①/② 게이트)"
  exit 1
fi

# ③ 스킬 15: 핸드오프 커밋일 때만 확인 토큰 요구
MSG="$(cat "$MSG_FILE" 2>/dev/null || true)"
if printf '%s' "$MSG" | grep -qi '\[handoff\]'; then
  if printf '%s' "$MSG" | grep -qiE '^Skill15-Reviewed:[[:space:]]*yes'; then
    echo ""
    echo "✅ ③ 스킬 15 문장 의미 대조 확인됨 (핸드오프 커밋)"
  else
    echo ""
    echo "❌ 커밋 차단 — 핸드오프 커밋입니다."
    echo "   스킬 15(.claude/skills/15_consistency_check.md)의 문장 의미 대조를 수행한 뒤,"
    echo "   커밋 메시지 본문에 아래 한 줄을 추가하세요:"
    echo ""
    echo "       Skill15-Reviewed: yes"
    echo ""
    exit 1
  fi
else
  echo ""
  echo "ℹ️  ③ 스킬 15(문장 의미 대조)는 개발 핸드오프 커밋에서만 필수입니다 — 이번 커밋은 생략."
  echo "    (핸드오프 커밋이면 메시지에 [handoff] 를 넣으세요.)"
fi

# ─── ④ 디자인 토큰 이탈 검사 (ax-design-system 에서 vendoring) ───────────────
# 기준 문서: .claude/design-system/{design-system,design-playbook,component-variants}.md
DESIGN="$SCRIPT_DIR/check-design-tokens.mjs"
echo ""
echo "▶ ④ 디자인 토큰 이탈 검사 (check-design-tokens.mjs)"

if [ ! -f "$DESIGN" ]; then
  echo "ℹ️  게이트 스크립트가 없어 건너뜁니다."
elif ! command -v node >/dev/null 2>&1; then
  echo "ℹ️  node 가 없어 건너뜁니다 (설치하면 자동 활성화)."
elif [ ! -d "$REPO_ROOT/ui/screens" ]; then
  echo "ℹ️  ui/screens/ 가 없어 검사 대상이 없습니다 — 건너뜁니다."
else
  DESIGN_STRICT=0
  if [ -f "$REPO_ROOT/.design-gate-strict" ] || [ "${DESIGN_GATE:-}" = "strict" ]; then
    DESIGN_STRICT=1
  fi

  DESIGN_OUT="$(node "$DESIGN" --root="$REPO_ROOT" --scope=ui/screens 2>&1)"
  RC4=$?

  if [ "$RC4" -eq 0 ]; then
    printf '%s\n' "$DESIGN_OUT" | sed -n '1,6p'
    echo "✅ ④ 디자인 토큰 이탈 없음 (범위: ui/screens)"
  elif [ "$DESIGN_STRICT" -eq 1 ]; then
    printf '%s\n' "$DESIGN_OUT"
    echo ""
    echo "❌ 커밋 차단 — 디자인 토큰 이탈(ERROR)을 먼저 해소하세요. (④ 게이트 · strict 모드)"
    echo "   기준: .claude/design-system/design-playbook.md 1.1 (토큰 이탈 금지)"
    exit 1
  else
    printf '%s\n' "$DESIGN_OUT" | sed -n '1,12p'
    echo ""
    echo "⚠️  ④ 디자인 토큰 이탈이 있습니다 — 조언 모드라 차단하지 않습니다."
    echo "   전체 목록: node $DESIGN --root=. --report"
    echo "   차단으로 켜기: 저장소 루트에 .design-gate-strict 생성 또는 DESIGN_GATE=strict"
  fi
fi

echo ""
echo "✅ 커밋 게이트 통과"
exit 0
