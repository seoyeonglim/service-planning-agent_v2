# Getting Started — 사용자 가이드

> ⤳ vendored from ax-design-system @ 9a6e7c5 · doc-sha e1b050698787 · 정본 변경 시 재동기화
> 원격은 `git@github.wrtn.club:wrtn-tech/ax-design-system.git` 브랜치 `develop`. 이 레포에서의 보관 위치는 `docs/` 가 아니라 `.claude/design-system/` 이다 — 이 레포의 `docs/` 는 고객 산출물 유출 방지를 위해 통째로 git 추적 제외이기 때문. 사유는 `design-playbook.md` "10. 프로젝트별 슬롯" 참조.

> ⤳ vendor: required — 도입한 레포의 진입 문서다. 게이트 2종을 어떤 순서로 돌리는지와 "토큰은 상속해 쓰는 것이지 새로 만드는 게 아니다" 라는 멘탈 모델이 여기에만 있다.

이 템플릿을 처음 쓰는 사람을 위한 진입 문서다. "무엇이 어디 있나"(README)와 "왜 그렇게 설계됐나"(ARCHITECTURE.md)와 달리, 이 문서는 **사용하는 입장에서 어떤 순서로 쓰면 되나**를 다룬다.

> **이 레포는 Next.js 16 + shadcn/ui 단일 패키지(`@wrtn/nextjs-shadcn`)다.** Figma 토큰 동기화(`/sync-figma` → `/apply-tokens`)와 리뷰 게이트(`/design-review`)가 shadcn 어휘를 전제로 작동한다. Vite 변형(`vite-shadcn`)과 MUI 패키지가 필요하면 아카이브 브랜치(`archive/vite-shadcn`, `archive/nextjs-mui`, `archive/vite-mui`)를 참조한다 — 동결 상태이며 유지보수되지 않는다.

> **핵심 멘탈 모델:** 이 레포를 그대로 떼어 쓰되, **디자인 토큰·규칙이라는 공유 진실을 벗어나지 않게 쓰는 것**이 목적이다. 토큰은 _상속해서 쓰는 것_ 이지 새로 만드는 게 아니다.

---

## 1. 실행한다

```bash
pnpm install
pnpm dev        # → http://localhost:3000
```

---

## 2. 코딩 전에 `/foundations` 와 `/components` 를 먼저 본다

화면을 짜기 전에:

- `/foundations` 에서 이미 존재하는 **시맨틱 토큰**(색·타이포 27종·radius·shadow·spacing)을 눈으로 확인한다. Dark / Light 토글로 양쪽 모드에서 어떻게 도는지도 본다.
- `/components` 에서 **쓸 수 있는 부품**을 확인한다. 카드에 보이는 것은 이미지가 아니라 실제로 렌더된 컴포넌트이고, 눌러 들어가면 variant 와 사용 지침이 있다.

이 단계의 목적은 **"내가 쓸 값은 이미 토큰으로 다 있다"를 체감**하는 것이다. 여기 없는 값을 코드에서 새로 만들지 않는다 — 없으면 가장 가까운 토큰으로 맞추고, 대체가 없을 때만 정본 레포의 `docs/proposals/` 에 신규 토큰 제안을 남긴 뒤 `ds-allow` 주석으로 제안 경로를 걸어 진행한다.

---

## 3. 화면 / 컴포넌트를 추가한다

1. 페이지 생성 — `src/app/<page>/page.tsx`
2. 색은 **시맨틱 Tailwind 클래스만** — `bg-surface-elevated`, `text-text-primary`, `bg-primary-main` …
   - 금지: 하드코딩 hex / `rgb()` / `bg-zinc-900` 같은 Tailwind 기본 팔레트 / `bg-[#1e1e23]` 같은 arbitrary value
3. 타이포는 `text-header-40` ~ `text-plain-12` 토큰 또는 `typography.{key}` helper
4. 컴포넌트는 `src/components/ui/` 에서 import — 호출법은 [`component-variants.md`](./component-variants.md) 를 따른다
5. 토큰 값 SSOT 는 [`design-system.md`](./design-system.md)

---

## 4. 벗어나면 안 되는 "공유 진실"의 위치

규칙은 흩어져 있지 않고 계층으로 정리돼 있다.

| 무엇                          | 어디                                            | 비고                                          |
| ----------------------------- | ----------------------------------------------- | --------------------------------------------- |
| 토큰 _값_ (색·타이포·…)       | [`docs/design-system.md`](./design-system.md)   | Figma 자동 동기화 산출물                      |
| 컴포넌트 _호출법_             | [`docs/component-variants.md`](./component-variants.md) | 사람이 수동 관리                         |
| 레이아웃·인터랙션·접근성      | [`docs/design-playbook.md`](./design-playbook.md) | RULE 은 필수 / PREFER 는 권장                 |
| 아키텍처 규칙                 | [`../ARCHITECTURE.md`](../ARCHITECTURE.md)       | barrel 최소화, 3+ 소비처일 때만 공용 추출, 100dvh 등 |
| Figma → 코드 동기화 전체 흐름 | [`docs/workflow.md`](./workflow.md)             | sync / apply 관계도                           |
| 코드 규칙 / 게이트 규율       | [`../AGENTS.md`](../AGENTS.md)                   | 레포 진입점                                   |

읽는 순서는 **`ARCHITECTURE.md` → `AGENTS.md` → 작업 중 필요할 때 `docs/*`** 면 충분하다.

---

## 5. 마무리 게이트 — `pnpm check:design` + `/design-review`

게이트는 **둘**이고 보완 관계다.

- **정적 게이트 `pnpm check:design`** (결정론·전수·매 PR) — `scripts/check-design-tokens.mjs` 가 `src/**` _전체_ 에서 하드코딩 색·primitive 팔레트·raw 타이포·임의값을 잡는다. authored 레이어 이탈은 ERROR(차단), vendored(`ui/`·shader) 이탈은 WARN(추적), 불가피한 예외는 `ds-allow` 주석으로 면제. **vendoring 한 레포는 이 스크립트를 가져가 자기 CI/verify 에 연결한다.** `/design-review` 가 diff 만 보느라 놓치는 vendored 드리프트까지 본다.
- **판단 게이트 `/design-review`** (사람 판단) — 정적 검사가 못 보는 시각 위계·craft·코드 어휘·playbook RULE 을 디자이너 리뷰 형식으로 본다.

UI 를 바꾸고 **커밋 푸시 / PR 생성 직전**, 먼저 `pnpm check:design` 으로 토큰 이탈을 0(ERROR) 으로 만든 뒤 `/design-review` 를 돌려 코드 어휘 위반·playbook RULE 위반이 없는지 디자이너 리뷰 형식으로 확인한다.

- **FAIL 0건** 이어야 게이트 통과. FAIL 이 있으면 수정 후 재실행한다.
- PR 본문에 리뷰 결과 요약(PASS, 또는 의도적으로 남긴 WARN 과 사유)을 적는다.
- 게이트 규율 전체는 [`../AGENTS.md`](../AGENTS.md) 의 "Design Review Gate" 섹션, 루브릭 전체는 [`.claude/commands/design-review.md`](../.claude/commands/design-review.md) 참조.

---

## 6. 템플릿으로 추출해 실제 프로젝트로 쓸 때 — 어떤 파일/폴더까지 가져가나

이 레포는 이미 단일 패키지 구조라, 새 프로젝트를 시작할 때는 **레포를 통째로 복제한 뒤 데모·작업 산출물만 걷어내면** 된다. (기존 앱에 DS 를 입히는 brownfield 적용은 `/setup-design-system` 커맨드가 담당한다.)

### 가져갈 것 ✅ (코어 — 그대로 유지)

| 대상                          | 위치                                                                 | 이유                                          |
| ----------------------------- | -------------------------------------------------------------------- | --------------------------------------------- |
| 테마·토큰                     | `src/theme/**` (`tokens.ts`, `types.ts`, `colorMode.ts`)             | 디자인 토큰의 코드 미러 — 핵심                |
| 토큰 CSS 변수                 | `src/app/globals.css`                                                | CSS 변수 + Tailwind @theme 매핑 SSOT          |
| 프로바이더                    | `src/providers/ThemeProvider.tsx`                                     | 테마 Context                                  |
| DS 컴포넌트                   | `src/components/ui/**`, `src/lib/typography.ts`                       | shadcn DS 부품 + 타이포 helper                |
| 공용 컴포넌트                 | `src/components/common/**` (실제 쓰는 것만)                          | `PageContainer` 등                            |
| 엔트리                        | `src/app/layout.tsx`                                                  | 앱 부팅                                       |
| 설정 파일                     | `package.json`, `tsconfig.json`, `eslint.config.mjs`, `.prettierrc`, `next.config.ts`, `postcss.config.mjs`, `components.json` | 빌드·린트·타입 인프라 |
| 디자인 토큰 정적 게이트       | `scripts/check-design-tokens.mjs` + `package.json` 의 `check:design` 스크립트 | 절대값(하드코딩 색·primitive 팔레트·raw 타이포·임의값) 금지를 매 PR 결정론으로 검사 — 새 레포의 CI/verify 에 연결 |
| 편집·커밋 훅                  | `.claude/hooks/design-token-guard.mjs`, `.claude/hooks/pre-commit-gate-reminder.mjs` + `.claude/settings.json` 의 `hooks` 등록 | 위 게이트를 편집 직후(파일 단위 즉시 검사)와 커밋 직전(게이트 리마인더)으로 당긴다 — `check:design` 스크립트와 함께 가야 동작 |
| 공유 규칙 문서                | `docs/design-system.md`, `docs/component-variants.md`, `docs/design-playbook.md`, `docs/layout-types/*.md`, `docs/workflow.md`, `docs/getting-started.md` | 토큰·어휘·레이아웃·화면 유형 SSOT |
| 아키텍처·기여 규칙            | `ARCHITECTURE.md`, `AGENTS.md`, `CLAUDE.md`                           | 크로스 커팅 규칙 + AI/기여 가이드             |
| 디자인 워크플로우 커맨드      | `.claude/commands/` (`sync-figma.md`, `apply-tokens.md`, `design-review.md`, `design-based-build.md`, `setup-design-system.md`) | 토큰 동기화·리뷰 게이트·화면 제작 진입·재동기화 유지 |
| 레포 인프라                   | `.gitignore`, `.husky/`, `.github/` (필요 시), `pnpm-lock.yaml`       | git·훅·CI                                    |

### 참고만 하고 교체/삭제 🔁 (데모 — 제품엔 불필요)

| 대상                          | 위치                                                                                  | 처리                                          |
| ----------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------- |
| 홈 데모 페이지                | `src/app/page.tsx`                                                                     | 실제 첫 화면으로 **교체**                     |
| 카탈로그 화면 전체            | `src/app/{get-started,foundations,components}/**`, `src/app/playground/**`(playbook), `src/components/common/SiteNav.tsx` | 토큰·부품 학습용 데모 — 개발 중 참고하다 출시 전 **삭제** |

> 💡 이 화면들은 "이미 있는 토큰·부품을 눈으로 익히는" 용도라 개발 초기에는 남겨두면 편하다. 다만 제품 코드에는 포함하지 말고, 구조가 손에 익으면 지운다. 규칙 자체는 `docs/` 문서가 SSOT 이므로 화면을 지워도 남는다.

### 버릴 것 ❌ (작업 산출물)

| 대상                          | 위치                                              | 이유                                  |
| ----------------------------- | ------------------------------------------------- | ------------------------------------- |
| OMC 작업 산출물               | `.omc/`, `.omx/`                                  | 에이전트 세션 상태 — 제품과 무관      |
| 빌드 산출물                   | `.next/`, `*.tsbuildinfo`, `test-results/`        | 재생성됨                              |
| 템플릿 메타                   | README 의 Jira 링크 등                            | 새 프로젝트 맥락으로 교체             |

### 추출 후 첫 점검

1. `pnpm install` → `pnpm dev` 가 뜨는지
2. `/foundations` 와 `/components` 가 정상 렌더되는지 — 토큰이 살아 있다는 신호
3. `docs/*` 링크와 `.claude/commands/` 가 새 경로에서도 유효한지
4. 첫 화면을 짠 뒤 `/design-review` 로 게이트 통과 확인

---

## 한 줄 요약

> **`/foundations` 와 `/components` 로 이미 있는 토큰·부품을 익히고 → 토큰·어휘·playbook 밖으로 나가지 않게 화면을 짜고 → `pnpm check:design` + `/design-review` 로 통과시킨다.**
>
> 떼어 쓸 때는 **레포를 통째로 복제해 `src/` 코어 + `docs/` 규칙 + `.claude/commands/` 를 유지하고**, playground 데모·`.omc`/빌드 산출물은 버린다.
