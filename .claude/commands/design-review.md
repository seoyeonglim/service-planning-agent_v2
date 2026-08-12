---
description: 변경된 UI/화면/컴포넌트를 디자이너가 관리하는 3대 기준 문서(design-system.md, component-variants.md, design-playbook.md)에 대조해 디자이너 리뷰 형식으로 평가한다. 커밋 푸시·PR 생성 전에 통과시켜야 하는 디자인 게이트.
argument-hint: '[--branch | --staged | <path...>] [--strict]'
allowed-tools: Read, Grep, Glob, Bash(git status:*), Bash(git diff:*), Bash(git merge-base:*), Bash(git rev-parse:*), Task
---

# /design-review — 디자인 기준 문서 대조 리뷰 게이트

이 커맨드의 **유일한 책임**: 이번 변경분 중 UI 코드를 디자이너가 관리하는 **3대 기준 문서**에
대조해, 디자이너가 리뷰하듯 **PASS / WARN / FAIL** 판정 리포트를 낸다.
코드를 직접 수정하지 않는다 — 평가만 한다. (수정은 결과를 받은 뒤 별도로 진행)

```
변경된 UI 코드  ──/design-review──▶  디자이너 리뷰 리포트 (PASS/WARN/FAIL + 수정 제안)
                       ▲
       ┌───────────────┼───────────────┐
  design-system.md      component-variants.md       design-playbook.md
   (토큰 값 SSOT)        (shadcn 코드 어휘 SSOT)      (레이아웃·인터랙션 기준선)
        └──────── 모두 .claude/design-system/ 하위 ────────┘
```

> - **이 커맨드는 read-only 다.** 파일을 고치지 않는다. authoring 과 review 는 별도 패스 — 같은 컨텍스트에서 셀프 승인하지 않는다.
> - 평가는 **리뷰 전용 subagent 에 위임**한다(아래 "실행 절차"). 메인 컨텍스트가 자기 작업을 자기가 통과시키지 않게 하기 위함.
> - **토큰 *값* 대조는 shadcn 어휘 코드에만 적용**한다. 본 레포는 전체가 shadcn 기반이므로 항상 적용 대상이다. (이 커맨드를 vendoring 한 다운스트림 레포에서 MUI 기반 코드가 섞여 있으면, 그 부분은 토큰 값 대조를 건너뛰되 playbook 의 레이아웃·인터랙션·접근성 RULE 은 동일하게 적용한다.)

---

## 입력 인자

`$ARGUMENTS` 의 옵션:

| 옵션        | 동작                                                                 |
| ----------- | -------------------------------------------------------------------- |
| (옵션 없음) | `--branch` 와 동일 (기본값)                                          |
| `--branch`  | 현재 브랜치 ↔ **기본 브랜치**의 merge-base 부터의 전체 diff 를 대상으로 평가 |
| `--staged`  | staged 변경분(`git diff --cached`)만 평가 — 커밋 직전 빠른 게이트    |
| `<path...>` | 지정한 파일/디렉토리만 평가                                          |
| `--strict`  | WARN(PREFER 이탈)도 FAIL 로 취급 — 게이트를 엄격하게                 |

---

## 실행 절차

### 1. 평가 대상 수집

옵션에 따라 변경 파일 목록과 diff 를 모은다.

- `--branch`(기본): 먼저 **기본 브랜치를 감지한다** — 브랜치 이름을 하드코딩하지 않는다. 레포마다 기본 브랜치가 `develop`/`main`/`master` 로 다르고, 이 커맨드는 vendoring 한 다운스트림 레포에서도 그대로 동작해야 한다.

  ```bash
  BASE="$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)"          # 예: origin/develop
  [ -z "$BASE" ] && git rev-parse --verify -q origin/develop >/dev/null && BASE=origin/develop
  [ -z "$BASE" ] && git rev-parse --verify -q origin/main    >/dev/null && BASE=origin/main
  [ -z "$BASE" ] && BASE=HEAD~1                                          # 폴백: 원격이 없는 레포
  MERGE_BASE="$(git merge-base HEAD "$BASE")"
  ```

  구한 `$MERGE_BASE` 로 `git diff $MERGE_BASE...HEAD --name-only` 로 파일 목록, `git diff $MERGE_BASE...HEAD` 로 패치를 얻는다. 작업 트리의 uncommitted 변경분도 `git status`/`git diff` 로 함께 포함한다.
  - **감지한 기준 브랜치를 리포트 머리에 적는다** (예: `대상: origin/develop...HEAD`). 잘못된 기준으로 넓거나 좁게 본 리뷰를 "통과" 로 오해하지 않기 위함이다.
- `--staged`: `git diff --cached`.
- `<path...>`: 해당 경로만.

수집한 파일 중 **UI 관련 파일만** 추린다 (`.tsx`/`.jsx`/`.css`/`globals.css`/`tokens.ts`/컴포넌트 디렉토리). 순수 설정·문서·테스트 파일만 바뀌었으면 "리뷰 대상 UI 변경 없음 — PASS" 로 즉시 종료한다.

평가 대상에 UI 코드가 포함되면 **정적 게이트도 함께 실행해 증거로 첨부**한다:
`pnpm check:design`.
ERROR 는 그 자체로 루브릭 A 의 FAIL 후보이고, WARN(vendored 레이어·v5 마이그레이션 백로그)은 리포트에 추적 항목으로 남긴다.

### 2. 기준 문서 로드

다음 3개를 읽어 체크 기준으로 삼는다. **추측 금지** — 실제 문서의 RULE/토큰/어휘를 근거로 평가한다.

- `.claude/design-system/design-system.md` — 토큰 _값_ SSOT (색·타이포·radius·shadow·spacing).
- `.claude/design-system/component-variants.md` — shadcn variant 호출법·utility 클래스 어휘 SSOT.
- `.claude/design-system/design-playbook.md` — 레이아웃·화면 레시피·인터랙션·접근성 기준선. **RULE/PREFER 강제력 어휘를 그대로 따른다.**
- `.claude/design-system/layout-types/01-workspace.md` — 화면 유형별 레시피.

> ⤳ 이 커맨드는 ax-design-system @ f430de0 에서 vendoring 했다. 정본 대비 로컬 변경은
> **기준 문서 경로(`docs/` → `.claude/design-system/`)뿐**이며 루브릭·판정 기준은 무수정이다.
> 이 레포는 `docs/` 를 통째로 git 추적 제외하므로 경로를 옮겼다.

### 3. 리뷰 lane 위임

`Task` 로 **리뷰 전용 subagent** 를 띄워, 수집한 diff + 3대 문서를 컨텍스트로 주고 아래 루브릭으로 평가시킨다. (OMC 환경이면 `code-reviewer` 또는 `designer` 에이전트, 아니면 일반 subagent.) 변경 규모가 크면 화면/컴포넌트 단위로 병렬 분할한다.

subagent 에게 주는 지시: **"디자이너 리뷰어"로서, 아래 루브릭의 각 항목을 변경된 코드에 대조해 PASS/WARN/FAIL 과 근거(파일:라인)를 매긴다. 코드를 수정하지 말고 평가만 한다."**

### 4. 평가 루브릭 (디자이너 리뷰 체크리스트)

**A. 토큰 이탈 (design-system.md 기준 — shadcn 어휘 코드에 적용)** — 위반 시 **FAIL**

- 색이 **v5 canonical semantic 토큰**(`bg-surface-elevated`, `text-text-primary`, `bg-primary-main`, `bg-status-error-subtle`, `text-icon-primary`…)만 쓰는가. 하드코딩 hex·`rgb()`·named color 없는가.
- **shadcn alias 금지** — `bg-background`, `text-foreground`, `bg-primary`, `bg-card`, `bg-muted`, `border-border`, `ring-ring`, `bg-destructive` 등과 v4 compat alias(`bg-surface-primary`, `bg-success-soft`, `text-text-primary-invert`…)를 컴포넌트/화면 코드에서 쓰지 않는가. alias 는 `globals.css` 호환 층 전용이다 (playbook 1.1 RULE, 예외: `ring-offset-background-primary`).
- **primitive 직접 사용 금지** — `mint-*`/`gray-*`/`red-*`/`amber-*`/`green-*`/`blue-*`/`alpha-*` 를 컴포넌트/화면 코드에서 직접 쓰지 않는가. Tailwind 기본 팔레트(`bg-zinc-900`, `text-slate-500`)는 당연히 금지.
- 타이포가 템플릿 27 토큰(`text-header-40`~`text-plain-12`) 또는 `typography.{key}` helper 인가. 생짜 `text-sm`/`text-xl`, 커스텀 타입스케일 재발명 없는가.
- radius/shadow/spacing 이 토큰만인가. 임의값(`rounded-[14px]`, `p-[13px]`) 없는가.
- 인라인 `style={{}}` 에 값 직접 박힘 없는가(토큰 `var(--…)` 참조 또는 className 만).
- **`ds-allow` 감사 예외** — 같은 줄 또는 바로 윗줄에 사유가 명시된 `ds-allow` 주석이 있는 위반은 FAIL 로 잡지 않는다 (승인된 예외). 단, 사유가 코드 실태와 맞지 않으면 WARN 으로 지적한다.

**B. 코드 어휘 (component-variants.md 기준)** — 위반 시 **FAIL**

- 컴포넌트 variant 호출법이 문서에 정의된 어휘를 따르는가. 임의 variant 재발명·문서에 없는 prop 조합 없는가.
- utility 클래스 사용이 문서 가이드와 일치하는가.

**C. 레이아웃·인터랙션·접근성 (design-playbook.md 기준)**

- **RULE 항목 위반 → FAIL**: 모바일 퍼스트, `lg`(1024) 사이드바→드로어, 탭 영역 ≥32×32px(정본 `design-playbook.md` 1.3c), 본문 한 줄 ≤80자, z-index/레이어링 규칙, 상태 처리(loading/empty/error), 토큰 이탈 금지 등.
- **PREFER 항목 이탈 → WARN**: 권장 치수·max-width·breakpoint·패딩 기본값 등. 이탈 자체는 허용이나 의도를 명시해야 한다.

**D. craft(권장)** — **WARN** 또는 코멘트

- 시각 위계·깊이·여백·제품감이 "규칙만 지킨 밋밋함"에 머물지 않는가. playbook 의 craft 철학 충족 여부.

### 5. 판정 + 리포트 출력

다음 형식으로 요약한다.

```
## 🎨 Design Review — <대상 요약>

판정: ✅ PASS  /  ⚠️ PASS (WARN N건)  /  ❌ FAIL (blocker M건)
check:design: ERROR N건 · WARN N건 · ds-allow 면제 N건

### ❌ FAIL (blocker) — 커밋/PR 전 반드시 수정
- [A. 토큰] <파일:라인> — <무엇이 왜 위반인지> → <수정 방향>

### ⚠️ WARN (PREFER 이탈 / craft) — 의도 확인 또는 개선 권장
- [C. PREFER] <파일:라인> — <이탈 내용> → <권장값 또는 사유 명시 요청>

### ✅ PASS — 충족 항목 요약
- A. 토큰 이탈 없음 / B. 코드 어휘 일치 / C. RULE 충족 …

### 다음 행동
- FAIL 있으면: 수정 후 /design-review 재실행
- WARN 만: 의도 PREFER 이탈이면 사유를 PR 설명에 적고 진행 가능
```

**게이트 판정 규칙:**

- **FAIL 0건** → 게이트 통과. 커밋 푸시·PR 진행 가능.
- **FAIL ≥1건** → 게이트 차단. 수정 후 재실행.
- `--strict` 면 WARN 도 차단으로 취급.

---

## 사용 위치

- **커밋 푸시 직전 / PR 생성 직전** 의 필수 게이트. AGENTS.md "Design Review Gate" 규율 참조.
- UI 변경이 포함된 작업을 "완료"로 보고하기 전.
- 토큰/variant 가 기준 문서에 없어 FAIL 이 나면, 임의값으로 때우지 말고 문서에 먼저 추가할지 디자이너(dana)에게 문의한다 — 문서가 SSOT 다.
