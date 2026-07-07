#!/bin/bash

# 서비스 기획 에이전트 - 세션 시작 훅
# 기존 프로젝트 현황을 파악하고 컨텍스트를 제공한다

DOCS_DIR="$(pwd)/docs"

echo "======================================"
echo "  서비스 기획 에이전트 시작"
echo "======================================"
echo ""

# docs/ 폴더가 없으면 신규 시작 안내
if [ ! -d "$DOCS_DIR" ]; then
  echo "📋 진행 중인 프로젝트가 없습니다."
  echo ""
  echo "새 프로젝트를 시작하려면 서비스 아이디어를 입력해주세요."
  echo "예) \"미용실 예약 관리 앱을 만들고 싶어요\""
  exit 0
fi

# docs/ 하위 프로젝트 목록 추출
projects=$(find "$DOCS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | xargs -I{} basename {})

if [ -z "$projects" ]; then
  echo "📋 진행 중인 프로젝트가 없습니다."
  echo ""
  echo "새 프로젝트를 시작하려면 서비스 아이디어를 입력해주세요."
  exit 0
fi

echo "📂 진행 중인 프로젝트 현황"
echo "--------------------------------------"

for project in $projects; do
  project_dir="$DOCS_DIR/$project"
  echo ""
  echo "🗂  [$project]"

  # Phase 1: PRD
  prd_count=$(find "$project_dir/prd" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$prd_count" -gt 0 ]; then
    prd_file=$(find "$project_dir/prd" -name "*.md" 2>/dev/null | head -1 | xargs basename 2>/dev/null)
    echo "  ✅ Phase 1 PRD       : 완료 ($prd_file)"
  else
    echo "  ⬜ Phase 1 PRD       : 미완료"
  fi

  # Phase 2: UI 문서 (4종)
  ia_exists=$([ -f "$project_dir/ui/01_information_architecture.md" ] && echo "✅" || echo "⬜")
  flow_exists=$([ -f "$project_dir/ui/02_user_flow.md" ] && echo "✅" || echo "⬜")
  spec_exists=$([ -f "$project_dir/ui/03_screen_spec.md" ] && echo "✅" || echo "⬜")
  design_exists=$([ -f "$project_dir/ui/04_design_direction.md" ] && echo "✅" || echo "⬜")

  ui_count=0
  [ "$ia_exists" = "✅" ] && ui_count=$((ui_count + 1))
  [ "$flow_exists" = "✅" ] && ui_count=$((ui_count + 1))
  [ "$spec_exists" = "✅" ] && ui_count=$((ui_count + 1))
  [ "$design_exists" = "✅" ] && ui_count=$((ui_count + 1))

  echo "  $ia_exists Phase 2 IA          : 서비스 구조도"
  echo "  $flow_exists Phase 2 User Flow  : 사용자 플로우"
  echo "  $spec_exists Phase 2 Screen Spec: 화면 명세서"
  echo "  $design_exists Phase 2 Design    : 디자인 방향"

  # Phase 3: UI 화면
  screen_count=$(find "$project_dir/ui/screens" -name "*.html" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$screen_count" -gt 0 ]; then
    echo "  ✅ Phase 3 UI 화면   : ${screen_count}개 생성 완료"
  else
    echo "  ⬜ Phase 3 UI 화면   : 미생성"
  fi

  # 다음 단계 안내
  echo ""
  if [ "$prd_count" -eq 0 ]; then
    echo "  👉 다음 단계: Phase 1 PRD 작성"
  elif [ "$ui_count" -lt 4 ]; then
    echo "  👉 다음 단계: Phase 2 UI 문서 작성 ($ui_count/4 완료)"
  elif [ "$screen_count" -eq 0 ]; then
    echo "  👉 다음 단계: Phase 3 UI 화면 생성"
  else
    echo "  🎉 모든 단계 완료"
  fi
done

echo ""
echo "--------------------------------------"
echo "계속할 프로젝트명을 말하거나, 새 아이디어를 입력해주세요."
echo ""
