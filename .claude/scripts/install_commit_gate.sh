#!/bin/bash
# ─────────────────────────────────────────────────────────────
# 커밋 게이트 설치기 (서비스 기획 에이전트)
#
# 프로젝트 저장소의 .git/hooks/commit-msg 에 게이트 훅을 설치한다.
# git 훅은 저장소마다 로컬로 설치해야 하므로(형상관리에 안 올라감),
# 새 프로젝트 저장소를 git init 한 뒤 한 번씩 실행한다.
#
# 사용법:
#   bash .claude/scripts/install_commit_gate.sh docs/[프로젝트명]
#   (인자 생략 시 현재 폴더에 설치)
# ─────────────────────────────────────────────────────────────
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$SCRIPT_DIR/commit_gate.sh"
TARGET="${1:-.}"

if [ ! -f "$GATE" ]; then
  echo "❌ commit_gate.sh 를 찾을 수 없습니다: $GATE"
  exit 1
fi

cd "$TARGET" 2>/dev/null || { echo "❌ 경로 없음: $TARGET"; exit 1; }

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "❌ git 저장소가 아닙니다: $TARGET"
  echo "   먼저 이 폴더에서 'git init' 하세요."
  exit 1
fi

HOOK_DIR="$(git rev-parse --git-dir)/hooks"
mkdir -p "$HOOK_DIR"
HOOK="$HOOK_DIR/commit-msg"

# 이미 우리 훅이 아닌 다른 commit-msg 훅이 있으면 백업
if [ -e "$HOOK" ] && ! grep -q "commit_gate.sh" "$HOOK" 2>/dev/null; then
  cp "$HOOK" "$HOOK.bak"
  echo "ℹ️  기존 commit-msg 훅을 $HOOK.bak 로 백업했습니다."
fi

cat > "$HOOK" <<EOF
#!/bin/sh
# 서비스 기획 에이전트 커밋 게이트 (install_commit_gate.sh 자동 생성 — 직접 수정 금지)
exec "$GATE" "\$1"
EOF
chmod +x "$HOOK"

echo "✅ 커밋 게이트 설치 완료"
echo "   훅:   $HOOK"
echo "   대상: $(basename "$(git rev-parse --show-toplevel)")"
echo ""
echo "   이제 이 저장소에서 커밋하면 ①추적성 ②정합성 검사가 자동 실행되고,"
echo "   ❌ 오류가 있으면 커밋이 차단됩니다."
echo "   개발 핸드오프 커밋은 메시지에 [handoff] + 'Skill15-Reviewed: yes' 를 넣으세요."
