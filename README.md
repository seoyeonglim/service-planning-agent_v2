# 서비스 기획 에이전트 (service-planning-agent_v2)

AI 코딩 에이전트(Claude Code / Codex CLI)를 **"10년 경력의 시니어 서비스 기획자"**로 동작시키는 에이전틱 워크플로우입니다.

핵심 아이디어는 하나입니다 — **AI가 문서를 바로 쓰지 못하게 막고, 실제 기획자처럼 "질문 → 확인 → 산출물 → 검증" 순서를 강제하는 것.** 이를 위해 세 겹의 장치로 구성됩니다:

1. **`CLAUDE.md`** — 전체 워크플로우 헌법 (Phase 0~4 순서, 게이트, 금지사항)
2. **`.claude/skills/` 15개 스킬** — 각 단계의 상세 실행 매뉴얼 (CLAUDE.md가 단계마다 "이 파일을 읽어라"고 지시)
3. **훅(hook) + 파이썬 스크립트** — 규칙 준수를 사람이 아닌 기계가 감시 (추적성 자동 검증, 스킬 동기화)

모든 산출물은 추적 ID로 사슬처럼 연결되며, 이 사슬이 끊기면 다음 단계로 진행할 수 없습니다.

```
REQ-###  요구사항   →  EC-##   엣지케이스
   ↓                    ↓
SC-##    화면      →  TC-###  테스트 케이스
   ↓
FS-###   기능명세   →  WBS 주차 배치
```

---

## 폴더 구조

| 덩어리 | 위치 | 한 줄 설명 |
|---|---|---|
| 📖 규칙서 | `CLAUDE.md`, `AGENTS.md`, `.claude/skills/` | AI에게 "이 순서로, 이렇게 일해라"를 알려주는 매뉴얼 |
| ⚙️ 자동 도구 | `.claude/scripts/`, `.claude/hooks/`, 설정 파일 | 규칙이 지켜졌는지 자동으로 검사·정리해주는 프로그램 |
| 📂 작업 결과물 | `docs/` | 실제 프로젝트에서 만들어진 기획 문서·화면들 (각 프로젝트가 독립 저장소로 별도 관리) |
| 📚 사람용 문서 | `README.md`, `guide/` | 이 워크플로우가 어떻게 돌아가는지 사람에게 설명 |

```
CLAUDE.md                      # 전체 작업 순서와 규칙 (가장 중요한 파일)
AGENTS.md                      # 위와 같은 내용의 Codex(다른 AI 도구)용 복사본
.claude/
├── skills/01~15_*.md          # 단계별 상세 매뉴얼 15개 + visual_generation/
├── scripts/                   # 검사기·스캐너·동기화·PDF 변환 (아래 자동화 장치 참조)
├── hooks/session_start.sh     # 시작할 때 "지금 어디까지 했더라?" 현황판
└── settings.local.json        # 검사기들이 자동으로 돌아가도록 연결하는 설정
.codex/skills/                 # 자동 생성된 복사본 (직접 수정 금지!)
.mcp.json                      # 고객이 준 워드/엑셀/PPT 파일을 읽을 수 있게 하는 설정
guide/                         # 사람용 상세 가이드 (스킬·검증·스캔 동작 원리)
docs/[프로젝트명]/              # 프로젝트별 산출물: prd/ ui/ fnspec/ wbs/ sow/ meetings/(회의록) assets/(와이어프레임) ref/(고객사 원자료)
```

> `docs/`는 고객사 정보가 담기므로 이 워크플로우 레포에는 올라가지 않습니다. 대신 각 프로젝트 폴더가 **그 자리에서 독립 git 저장소**가 되어 팀 GitHub(wrtnlabs)의 비공개 저장소로 따로 관리됩니다 — 화이트리스트 추적(prd·ui·fnspec·meetings·assets/wireframes만), ref/(고객사 원자료·PII)·sow/·wbs/ 등 나머지는 로컬 전용. 하위 폴더 구조는 [사용 방법](#사용-방법)의 저장 규칙 참조.

---

## Phase별 워크플로우

```
Phase 0  프로젝트 경로 설정   → 프로젝트명 확인, docs/[프로젝트명]/ 생성
Phase 1  PRD 작성            → 스킬 01→02→03→04→06→05 순서로 실행
Phase 2  UI 문서 4종          → 스킬 07→08→09→10
Phase 3  UI 화면 생성          → 스킬 11 + visual_generation
Phase 4  개발 핸드오프         → 스킬 12(기능명세서) → 13(WBS)
운영     변경 관리            → 스킬 14 (v1.0 확정 후 변경·추가·삭제 요청 처리)
운영     정합성 검증          → 스킬 15 (3계층: 추적성 → 기계 정합성 → 의미 대조)
```

- Phase 3과 Phase 4는 서로 의존하지 않아 **병행 가능**합니다.
- 각 Phase의 종료에는 **이중 게이트**가 있습니다:
  1. **사용자 승인** — "맞아요" 확인 전까지 다음 단계 진행 금지
  2. **자동 검증** — `python3 .claude/scripts/validate_traceability.py --strict` 실행, ❌ 오류 0이어야 통과

### 공통 운영 규칙 (모든 Phase)

- 각 기능은 `REQ-###` ID로 관리하고, 이름이 바뀌어도 ID는 유지
- 제안한 규칙/결정은 **ADR(결정사항 로그)** 형태로 기록 — 배경/대안/선택/이유/영향
- **버전 생애주기**: 초안(v0.x)은 git 커밋으로 변경 추적, v1.0 확정 이후엔 변경 1건마다 **변경 기록(CR-###)**을 `prd/CHANGELOG.md`에 작성 (대상/AS-IS/TO-BE/변경 범위/사유/승인 6항목)
- **문서 서열(내용 충돌 중재)**: PRD > UI 문서 > 기능명세서·화면 HTML > WBS — 내용이 어긋나면 상류가 옳고 하류를 고침, 상류(PRD) 수정은 CR로
- 미결(❓) 항목이 남아 있으면 다음 단계 진입 금지
- 선택지가 있는 질문은 반드시 `AskUserQuestion` 도구 사용

### 공통 금지사항

- 질문 없이 바로 문서 작성 금지
- PRD 없이 UI 문서, UI 문서 없이 UI 생성, 화면 명세 없이 기능명세서, 기능명세서 없이 WBS 작성 금지
- 기획 문서에 기술 구현 방법 기재 금지
- 추상적 표현 금지 — "편리한", "빠른", "쉬운" → 구체적 수치·조건으로 대체
- 영문 더미 데이터 사용 금지 (모든 UI 라벨·더미 데이터는 한국어)
- 외부 이미지 생성 API 호출 금지 — 모든 시각 산출물은 HTML/Mermaid로 직접 작성

---

## 스킬 한눈에 보기

각 스킬의 상세 규칙·게이트·산출물 형식은 **[guide/skills.md](guide/skills.md)** 참조.

| 단계 | 스킬 | 하는 일 |
|---|---|---|
| Phase 1 | 01 문제 정의력 | 솔루션 요청 뒤에 숨은 진짜 문제를 5 Whys와 질문 5개로 찾기 |
| | 02 사용자 관점 전환 | 페르소나 2명(정해린·한승우)을 판단 기준으로 강제, 추상어 금지 |
| | 03 구조화 능력 | REQ 채번, 기능 트리, MUST/SHOULD/NICE, MVP 경계 확정 |
| | 04 엣지케이스 감지 | 6개 카테고리 22개 질문으로 정상 플로우의 구멍 찾기 (EC) |
| | 05 문서 작성 노하우 | PRD 15개 섹션 템플릿 조립 + 변경 기록(CR) 형식 규칙 |
| | 06 테스트 케이스 도출 | REQ·EC를 Given-When-Then으로 번역 (TC) — 05보다 먼저 수행 |
| Phase 2 | 07 서비스 구조도 (IA) | REQ를 화면 구조(SC)로 변환, 화면 누락 방지 |
| | 08 사용자 플로우 | 정상/분기/예외 경로를 Mermaid로 — 예외엔 복귀 지점 필수 |
| | 09 화면 명세서 | 화면당 5항목(데이터·액션·상태·입력 규칙·연결)을 추측 없이 명세 |
| | 10 디자인 방향 | 질문 4개 → 컬러·타이포·레이아웃 등 시스템 값 5가지 확정 |
| Phase 3 | 11 UI 생성 | 화면당 구조도→와이어프레임→주석 도해→본 HTML 4단계 확인 생성 |
| | visual_generation | 외부 API 없이 HTML/Mermaid로 시각 자료 3종(Type A/B/C) 제작 |
| Phase 4 | 12 기능명세서 | REQ를 FS-###로 분해 — 입력→처리→출력→예외 4칸 완결 |
| | 13 WBS 작성 | Epic=REQ, Story=FS를 가용일 기준 주차에 배치 + 리소스판 |
| 운영 | 14 변경 요청 처리 | v1.0 이후 자연어 요청을 판별(변경 A / 삭제=A변형·폐기 / 추가 B) 후 파일별 컨펌으로 반영 |
| 운영 | 15 내용 정합성 검증 | 3계층(추적성→기계 정합성→의미 대조)으로 문서 간 충돌 적발 — [결정]은 건별 사용자 확인 |

---

## 자동화 장치

`.claude/settings.local.json`에 두 개의 훅이 등록되어 있습니다:

| 훅 | 시점 | 실행 내용 |
|---|---|---|
| `Stop` | Claude 응답이 끝날 때마다 | `validate_traceability.py` (advisory 모드 — 차단 없이 현황 출력) |
| `PostToolUse` | Edit/Write/MultiEdit 직후 | `sync_codex_skills.py --quiet` (스킬 수정 시 .codex 자동 동기화) |

### 스크립트

- **`validate_traceability.py`** — 요구사항 추적성 채점기: 고아(정의만 있음)·유령(정의 없이 참조) 적발, MUST 커버리지 검사. `--strict`가 Phase 게이트. → [동작 원리 상세](guide/traceability.md)
- **`consistency_check.py`** — 내용 정합성 검사기(기계 판정): FS 우선순위 상속·단계 일치, MUST FS의 WBS 배치, 화면별 산출물 존재, 폐기 REQ 활성 참조, ID 중복. 문장 의미 충돌은 스킬 15의 에이전트 의미 대조가 담당
- **`impact_scan.py`** — 변경 영향 범위 수색기: "이 ID를 바꾸면 어느 문서를 같이 봐야 하지?"에 파일+줄 번호 체크리스트로 답함. → [동작 원리 상세](guide/impact-scan.md)
- **`sync_codex_skills.py`** — `.claude/skills/NN_name.md` 원본에서 `.codex/skills/NN-name/SKILL.md`를 자동 생성. `--check`(드리프트 점검), `--prune`(원본 삭제분 정리)
- **`make_pdf.sh`** — 기획서 md → 고객 전달용 PDF (Mermaid→PNG 치환 → pandoc → weasyprint). 사전 요구: `brew install pandoc weasyprint`
- **`hooks/session_start.sh`** — 세션 시작 시 프로젝트별 Phase 진행 현황판 출력 (수동 실행용)

### MCP 서버

`.mcp.json`에 **markitdown** 서버가 등록되어 있어, 고객사가 제공한 오피스 문서(docx/pptx/xlsx)를 마크다운으로 변환해 읽을 수 있습니다 (`ref/` 폴더의 RFP·정의서·매뉴얼 분석용).

---

## 멀티 에이전트 지원

같은 워크플로우를 **Claude Code와 Codex CLI 양쪽에서** 동일하게 운영하기 위한 구조입니다:

- **지침**: `CLAUDE.md`(원본, SSOT) ↔ `AGENTS.md`(Codex용 사본) — 내용이 어긋나면 CLAUDE.md가 우선
- **스킬**: `.claude/skills/NN_name.md`(원본) → `.codex/skills/NN-name/SKILL.md`(자동 생성) — PostToolUse 훅이 수정 시마다 자동 동기화
- 스킬을 고칠 때는 반드시 `.claude/skills/` 원본만 수정합니다. `.codex/` 복제본 직접 수정 금지

---

## 사용 방법

1. 이 폴더에서 Claude Code(또는 Codex CLI)를 실행
2. 서비스/기능 아이디어를 입력 — 예) `"미용실 예약 관리 앱을 만들고 싶어요"`
3. 에이전트가 프로젝트명을 물은 뒤(Phase 0), 문제 정의 질문부터 시작(Phase 1)
4. 각 단계 산출물을 확인하고 "맞아요"로 승인하면 다음 단계로 진행
5. 기존 프로젝트 재진입 시 `docs/` 하위 폴더명을 말하면 이어서 진행 (현황판: `bash .claude/hooks/session_start.sh`)

### 산출물 저장 규칙

| 산출물 | 경로 |
|---|---|
| PRD | `docs/[프로젝트명]/prd/` |
| UI 문서 4종 | `docs/[프로젝트명]/ui/` |
| 화면 HTML | `docs/[프로젝트명]/ui/screens/` |
| 와이어프레임·주석 도해 | `docs/[프로젝트명]/assets/wireframes/` |
| 기능명세서 | `docs/[프로젝트명]/fnspec/` |
| WBS | `docs/[프로젝트명]/wbs/` |
| 회의록 (협의·미팅 기록) | `docs/[프로젝트명]/meetings/` |
| 고객사 원자료 (git 추적 안 함 — 로컬 전용) | `docs/[프로젝트명]/ref/` |

> **형상관리 이중 구조**: 워크플로우 레포에는 `docs/` 하위 프로젝트가 `.gitignore`로 제외되어 뼈대만 올라갑니다. 각 프로젝트 폴더는 그 자리에서 독립 git 저장소로 초기화해 팀 GitHub(wrtnlabs) 비공개 저장소로 따로 푸시합니다. 프로젝트 저장소에는 **prd · ui · fnspec · meetings · assets/wireframes만 추적**(화이트리스트)하고 ref(원자료)·sow(계약)·wbs(내부 일정)·diagrams·_archive는 로컬 전용입니다. 프로젝트 작업 중 "커밋해/푸시해"는 그 프로젝트 저장소에만 반영되며, 푸시 전 고객 PII(상담 데이터·이메일 등)가 스테이징되지 않았는지 점검하는 게이트를 거칩니다.

---

## 상세 가이드

- **[guide/skills.md](guide/skills.md)** — 스킬 상세 (01~15 + visual_generation): 각 스킬의 규칙·게이트·산출물 형식
- **[guide/traceability.md](guide/traceability.md)** — 추적성 검증의 동작 원리: validate_traceability.py가 무엇을 어떻게 검사하는가
- **[guide/impact-scan.md](guide/impact-scan.md)** — 변경 영향 스캔의 동작 원리: impact_scan.py 사용법과 CR 작성 3단계
