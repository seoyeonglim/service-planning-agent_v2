---
name: visual-generation
description: 기획 문서 보완용 시각 자료 생성 스킬. 사용자가 "도식화", "시각화", "와이어프레임", "플로우 다이어그램", "UI 컨셉", "기획 도해"를 요청하거나, Phase 2 화면 명세 완료 후, Phase 3 본 HTML 생성 직전에 호출한다. 모든 산출물은 HTML/Mermaid로 작성하며 외부 이미지 생성 API를 사용하지 않는다.
disable-model-invocation: true
allowed-tools: Read, Write, Edit
argument-hint: "[project-name] [sc-id 또는 req-id] [label]"
---

# 시각 자료 생성 (Visual Generation)

기획 문서를 보완하는 시각 자료를 **HTML / Mermaid로 직접 작성**한다.
외부 이미지 생성 API(예: Gemini)는 사용하지 않는다.

- **Type A**: 서비스 플로우 다이어그램 → **Mermaid** (PRD / 사용자 플로우 보완)
- **Type B**: UI 컨셉 와이어프레임 → **저해상도 HTML**(그레이스케일) (화면 명세 레이아웃 보완)
- **Type C**: 기획 도해 / 주석 HTML 도해 → **HTML + 콜아웃 오버레이** (UI 동작 규칙·조건·분기를 말풍선으로 설명)

인수가 전달된 경우: `$ARGUMENTS`

> **진행 모드와 Type B:** Type B(저해상도 와이어프레임)는 **Quick 모드의 종료 산출물**이다. Quick에선 여기서 방향·플로우를 확정하고 사용자 승인 후 멈춘다. Full 모드에선 Type B가 고해상도 UI로 가기 전 중간 확인 단계다. (CLAUDE.md "진행 모드 선택" 참조)

> 상세 작성 규칙 및 Phase 통합 지점은 [REFERENCE.md](REFERENCE.md) 참조

---

## Step 1: 컨텍스트 파악

1. 현재 작업 문서에서 `REQ-###` 또는 `SC-ID` 확인
2. 생성 유형 결정

| 상황 | 유형 | 도구 |
|------|------|------|
| PRD / 사용자 플로우 흐름 보완 | Type A | Mermaid |
| 화면 명세서 레이아웃 컨셉 보완 | Type B | 저해상도 HTML |
| UI 동작 규칙·조건·분기를 콜아웃으로 설명 | Type C | HTML + 콜아웃 |

---

## Step 2: 작성

### Type A — Mermaid 플로우 다이어그램

- `flowchart`/`stateDiagram` 사용
- 정상 경로(Happy Path) 먼저, 분기 조건은 한국어 라벨로 명시
- 노드는 최대 10개, 초과 시 관련 단계를 하나로 그룹화
- 해당 문서(PRD / `02_user_flow.md`) 내 코드블록으로 **인라인** 삽입

### Type B — 저해상도 HTML 와이어프레임

- 그레이스케일(회색 박스/플레이스홀더)만 사용, 색·아이콘·실제 디자인 배제
- 화면 명세서의 표시 데이터·레이아웃 힌트를 한국어 더미 데이터로 배치
- "미완성 컨셉"임이 드러나는 와이어프레임 룩 유지(테두리·플레이스홀더 위주)
- 상태별로 작성 (기본상태 / 빈상태 / 오류상태 등) — 상태별 파일 분리 또는 **한 파일 내 상태 패널 병렬 배치** 중 택1 (병렬 배치 시 파일명은 `-기본` 하나로 통일)

### Type C — 주석 HTML 도해 (Annotated)

- Type B 와이어프레임 위에 **절대위치 콜아웃(말풍선) 오버레이**로 동작 규칙 표기
- 화면 명세서의 **동작 조건·분기·제약·트리거**를 콜아웃 텍스트로 명시
- 콜아웃은 색상으로 의미 구분 (아래 가이드)

**콜아웃 색상 가이드:** 색상별 의미는 [REFERENCE.md](REFERENCE.md)의 Type C 색상표(정본)를 따른다.

> 콜아웃·라벨은 반드시 한국어. 영문 UI 라벨 사용 금지.

---

## Step 3: 저장

| 유형 | 저장 위치 | 형식 |
|------|-----------|------|
| Type A | 해당 문서 내 인라인 | Mermaid 코드블록 |
| Type B | `docs/[프로젝트명]/assets/wireframes/wf-[SC-ID]-[label].html` | HTML 파일 |
| Type C | `docs/[프로젝트명]/assets/wireframes/annotated-[SC-ID]-[label].html` | HTML 파일 |

---

## Step 4: 문서 연결 및 사용자 확인

생성물을 해당 문서 관련 섹션에 연결:

```markdown
<!-- SC-ID | 화면명 - 상태 -->
[와이어프레임: 화면명](../assets/wireframes/wf-SC-ID-상태명.html)
```

연결 후 **AskUserQuestion**으로 다음 단계를 확인한다:
- "이 방향으로 본 HTML 생성 진행"
- "와이어프레임 수정 후 재확인"
- "건너뜀"

---

## 완성 체크리스트

- [ ] `REQ-###` 또는 `SC-ID`가 파일명과 문서 주석에 포함되었는가?
- [ ] 저장 경로가 `docs/[프로젝트명]/assets/` 하위인가?
- [ ] 문서에 산출물이 (Mermaid 인라인 또는 상대 경로 링크로) 연결되었는가?
- [ ] 한국어만 사용했는가?
- [ ] Type C의 경우 콜아웃 내용이 기획서 동작 규칙과 일치하는가?
- [ ] 외부 이미지 생성 API를 호출하지 않았는가? (모두 HTML/Mermaid)
- [ ] 사용자 확인을 받았는가?
