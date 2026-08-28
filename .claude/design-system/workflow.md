# Design System Sync Workflow

> ⤳ vendored from ax-design-system @ 9a6e7c5 · doc-sha 49a8afe7909a · 정본 변경 시 재동기화
> 원격은 `git@github.wrtn.club:wrtn-tech/ax-design-system.git` 브랜치 `develop`. 이 레포에서의 보관 위치는 `docs/` 가 아니라 `.claude/design-system/` 이다 — 이 레포의 `docs/` 는 고객 산출물 유출 방지를 위해 통째로 git 추적 제외이기 때문. 사유는 `design-playbook.md` "10. 프로젝트별 슬롯" 참조.

> ⤳ vendor: required — "디자인 시스템 적용 우선순위" 3계층(토큰 → DS 컴포넌트 → 바닐라 shadcn)이 여기에 있고 `component-variants.md` 가 이를 근거로 가리킨다. 앞쪽의 Figma 동기화 절차는 정본 전용이다 — 소비 레포에는 `/sync-figma`·`/apply-tokens` 커맨드를 주지 않으므로(`setup-design-system.md` 커맨드 표), 그 부분은 "토큰 값이 어디서 오는지" 의 배경으로만 읽는다.

> Figma 디자인 시스템 → 코드까지의 토큰/variant 흐름 전체를 한 눈에 정리한 문서.
> 새로 합류한 사람이 "어떤 파일을 어느 순서로 건드려야 하는가" 를 알 수 있도록 의도된 단일 길잡이.

이 레포는 디자인 시스템을 **자동 동기화 영역** 과 **수동 관리 영역** 두 갈래로 분리한다. 자동 영역은 Figma 가 진실의 원본이고, 수동 영역은 사람이 코드 어휘를 결정한다.

---

## 전체 관계도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                              ▶▶▶  자동 동기화 영역  ◀◀◀                     │
│                                                                         │
│   ┌──────────┐                                                          │
│   │  Figma   │                                                          │
│   │ (BX 토큰) │                                                          │
│   └────┬─────┘                                                          │
│        │                                                                │
│        │  /sync-figma <design-system-frame-URL>                         │
│        │  (.claude/commands/sync-figma.md)                              │
│        ▼                                                                │
│   ┌────────────────────────────────────────────────┐                    │
│   │ docs/design-system.md                          │   ◀ 토큰 *값* SSOT   │
│   │   1번 섹션 primitive scales (mint / gray / status)   │                    │
│   │   2번 섹션 semantic tokens (surface / text / ...)    │                    │
│   │   3번 섹션 typography (27 tokens)                    │                    │
│   │   4번 섹션 radius / 5번 섹션 shadow / 6번 섹션 spacing           │                    │
│   └────┬───────────────────────────────────────────┘                    │
│        │                                                                │
│        │  /apply-tokens [--dry-run]                                     │
│        │  (.claude/commands/apply-tokens.md)                            │
│        ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ src/app/globals.css            ◀ CSS 변수 + Tailwind v4 매핑       │  │
│   │ src/theme/tokens.ts            ◀ JS 미러 (playground / 코드젠용)    │  │
│   └────┬─────────────────────────────────────────────────────────────┘  │
│        │                                                                │
│                                                                         │
│                              ▶▶▶  수동 관리 영역  ◀◀◀                       │
│        │                                                                │
│        ▼                                                                │
│   ┌─────────────────────────────────────────────────┐                   │
│   │ docs/component-variants.md                      │  ◀ 호출법 SSOT     │
│   │   1번 섹션 cva variant 표 (Button / Badge / Alert)    │                   │
│   │   2번 섹션 Tailwind utility 클래스 표                 │                     │
│   │   3번 섹션 typography helper                          │                   │
│   │   6번 섹션 새 토큰/variant 추가 절차                  │                       │
│   └────┬────────────────────────────────────────────┘                   │
│        │                                                                │
│        │ 참조                                                            │
│        ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ src/components/ui/*             ← shadcn primitive (cva)        │   │
│   │ src/components/common/*         ← 앱 공용 레이아웃              │   │
│   │ src/lib/typography.ts           ← 27 토큰 helper                │   │
│   │ AGENTS.md                       ← Design Token Enforcement 규칙 │   │
│   │ README.md                       ← 레포 진입점                   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

```

---

## 노드별 역할 / 편집 정책

| 노드                             | 역할                                                                                                                                     | 편집 정책                                                                           |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Figma**                        | BX 디자인 어휘의 원본                                                                                                                    | 디자이너가 Figma 에서 변경. 사람이 손으로 hex 를 코드에 박지 않는다                 |
| **`/sync-figma`**                | Figma frame → `docs/design-system.md` 생성/갱신                                                                                          | 슬래시 커맨드. node-id 가 포함된 frame URL 필수. 결과물은 매번 덮어쓰기             |
| **`docs/design-system.md`**      | 토큰 _값_ SSOT (BX 슬래시 표기)                                                                                                          | **직접 편집 금지** — `/sync-figma` 가 덮어쓰는 산출물                               |
| **`/apply-tokens`**              | DS 의 _값_ 을 코드에 일괄 반영                                                                                                           | 슬래시 커맨드. `--dry-run` 지원 — 매핑 _구조_ 는 건드리지 않음                      |
| **`globals.css`**                | CSS 변수 (primitive → semantic → shadcn alias) + Tailwind v4 `@theme inline`                                                             | 값 갱신은 `/apply-tokens` 가 담당. 새 매핑 _구조_ 는 사람이 추가                    |
| **`theme/tokens.ts`**            | JS 미러 (playground / 타입 체크 / 코드젠 보조)                                                                                           | `/apply-tokens` 가 globals.css 와 동시 갱신                                         |
| **`docs/component-variants.md`** | shadcn 코드 어휘 SSOT (variant 호출법, utility 클래스 표)                                                                                | **사람이 수동 관리** — 새 variant 추가 시 갱신. 토큰 _값_ 변경과 무관               |
| **`components/ui/*.tsx`**        | shadcn 기반 모든 DS 컴포넌트 — 단일 부품(Button, Input 등) + 조합 컴포넌트(Dialog, Sidebar, Menu 등). Figma `177:1671` + `219:5779` 대응 | 토큰 클래스만 사용. raw hex / Tailwind primitive 클래스 / arbitrary value 금지      |
| **`AGENTS.md`**                  | Design Token Enforcement 규칙 (7원칙 + 토큰 카테고리 표)                                                                                 | 정책 변경 시 사람이 수동 갱신                                                       |

---

## 시나리오별 절차

### 1) 디자이너가 Figma 에서 색상 hex 만 바꿨다

토큰 _값_ 만 변경. **이름·구조는 그대로**. 한 번의 명령으로 끝난다 (`/sync-figma` 가 성공 시
`/apply-tokens` 를 자동 chain 호출).

```bash
/sync-figma <design-system-frame-URL>
# ↓ 내부에서 자동으로
#   1. docs/design-system.md 갱신
#   2. /apply-tokens chain 호출 → globals.css + tokens.ts 갱신 + verify
```

sync 결과를 검토한 뒤 직접 적용하고 싶다면:

```bash
/sync-figma <URL> --no-apply               # chain 생략, sync 만 수행
# 검토 후
/apply-tokens                              # 또는 /apply-tokens --dry-run
```

`docs/component-variants.md`, `components/ui/*`, `AGENTS.md` 는 **건드릴 필요 없음**.

### 2) 디자이너가 새 토큰 카테고리를 추가했다 (예: motion)

토큰 _구조_ 가 확장됨. **자동 + 수동 영역 모두 손봐야 한다**. 자동 chain 은 의도적으로 생략하고
중간에 사람이 매핑을 박는다.

```bash
# 1. SSOT 갱신 (chain 생략 — 매핑이 아직 없으므로 apply-tokens 가 새 카테고리를 무시함)
/sync-figma <URL> --no-apply               # docs/design-system.md 에 7번 섹션 motion 추가

# 2. 매핑 구조 결정 (사람)
#    - src/app/globals.css 에
#      --motion-* 시맨틱 + Tailwind @theme inline 매핑 추가
#    - src/theme/types.ts 에 인터페이스 추가
#    - src/theme/tokens.ts 에 기본 객체 추가

# 3. 값 일괄 반영
/apply-tokens                              # 새 매핑이 박힌 상태에서 값만 박제

# 4. 코드 어휘 가이드 갱신 (사람)
#    - docs/component-variants.md 에 motion 표 추가
#    - AGENTS.md 의 토큰 카테고리 표 갱신
```

> 만약 1번을 `--no-apply` 없이 실행하면 `/apply-tokens` 가 "DS 에 새 카테고리(`motion`)
> 매핑이 globals.css 에 없습니다" 안전 가드로 거부하고 사람의 개입을 요청한다 — 의도된 안전망.

### 3) 새 컴포넌트 variant 만 추가한다 (예: `Button variant="brand-glow"`)

토큰은 그대로, _호출법_ 만 확장.

```bash
# 자동 동기화 영역은 손대지 않음

# 1. cva 정의 추가 (사람)
#    - src/components/ui/button.tsx 의 variants 블록에 추가

# 2. SSOT 갱신 (사람)
#    - docs/component-variants.md 1번 섹션 Button 표에 variant 행 추가
#    - AGENTS.md "shadcn/ui 컴포넌트 커스터마이징 정책" 표에도 동기화

# 3. 검증
pnpm verify
```

### 4) 토큰 값을 코드에서만 임시로 바꿔보고 싶다

**금지된 패턴**. design-system.md 가 SSOT 이므로 코드에서 직접 hex 를 박는 것은 enforcement 규칙(`AGENTS.md` "Design Token Enforcement") 위반. 실험은 Figma 에서 하고 `/sync-figma` 로 가져온다.

---

## 디자인 시스템 적용 우선순위 (PoC / 다운스트림 프로젝트용)

이 템플릿을 다른 프로젝트(PoC, 신규 서비스)에 가져다 쓸 때 따라야 하는 **3-계층 fallback 체인**. 새 화면을 만들거나 새 컴포넌트가 필요할 때 아래 순서로 결정한다.

```
┌─ 계층 1 ─ 토큰 (타협 불가) ──────────────────────────────────┐
│  색상 · 타이포 · radius · shadow · spacing                  │
│  → 모든 컴포넌트가 무조건 따른다.                              │
│  → raw hex / Tailwind primitive class / arbitrary value 금지. │
│  SSOT: docs/design-system.md (Figma 141:51 자동 동기화)        │
└────────────────────────────────────────────────────────────┘
                          ↓ 그 위에서
┌─ 계층 2 ─ Figma 정의 컴포넌트 (우리 DS) ──────────────────────────┐
│  Figma 에 정의된 모든 컴포넌트 — 단일 부품 + 조합 컴포넌트.         │
│  → 있으면 무조건 우선 사용.                                       │
│  현재 코드 구현:                                                  │
│    src/components/ui/*.tsx                                      │
│  shadcn 기반 + 계층 1 토큰 적용 완료.                              │
│  대응 Figma node: 177:1671 (단일 부품) + 219:5779 (조합)            │
│  SSOT: docs/component-variants.md 의 "Figma 정의 컴포넌트 카탈로그"│
└────────────────────────────────────────────────────────────┘
                          ↓ 계층 2 에 없을 때만
┌─ 계층 3 ─ 바닐라 shadcn + 계층 1 토큰 ────────────────────────┐
│  계층 2 에 없는 컴포넌트 (예: Accordion, Dialog, Tooltip).      │
│  → pnpm dlx shadcn@latest add <name> 으로 새로 가져온다.       │
│  → 가져오자마자 raw 색상을 계층 1 토큰 클래스로 갈아 끼운다.    │
│      (예: bg-zinc-900 → bg-surface-primary)                  │
│  → 그대로 두면 안 됨. shadcn 기본 팔레트 클래스 금지.            │
└────────────────────────────────────────────────────────────┘
```

### 적용 규칙 요약

| 상황                                      | 어떻게                                                           |
| ----------------------------------------- | ---------------------------------------------------------------- |
| 새 화면에 Button / Sidebar / Menu 등 필요 | 계층 2 — `ui/` 에서 import 해 사용                               |
| 새 화면에 Accordion 필요 (DS 에 없음)     | 계층 3 — `shadcn add accordion` → 색만 계층 1 토큰으로 갈아 끼움 |
| 컴포넌트에 임의 색상 적용 필요            | ❌ 금지. 토큰만 사용                                             |
| Figma 에 새 컴포넌트 디자인 발견          | PM/디자이너 확정 후 계층 2 로 승격 (별도 PR)                     |

### 계층 3 → 계층 2 승격 정책

**현재 미정.** 자주 쓰이는 계층 3 컴포넌트가 계층 2 로 자동 승격될지, 디자이너 판단으로만 승격될지는 운영하면서 결정한다.

---

## MUI / Vite 변형은 어디로 갔나

구 모노레포의 나머지 패키지(`@wrtn/nextjs-mui`, `@wrtn/vite-mui`, `@wrtn/vite-shadcn`)는
2026-07 폴리레포 전환 때 아카이브 브랜치(`archive/nextjs-mui`, `archive/vite-mui`,
`archive/vite-shadcn`)로 보존됐고 유지보수되지 않는다.

- MUI 는 토큰 어휘(`theme.palette.*`)가 shadcn 과 1:1 매핑되지 않아 원래부터 본 워크플로우의
  대상이 아니었다. 이 원칙은 다운스트림 프로젝트(brownfield MUI 앱)에 DS 를 적용할 때도
  동일하다 — `/setup-design-system` 커맨드 참조.
- vite-shadcn 변형이 필요하면 `archive/vite-shadcn` 브랜치를 참조한다 (토큰 구조는 동결
  시점 기준 본 레포와 동일).

---

## 검증 / Foundations

`/foundations` 가 자동 동기화 결과의 시각 검증 도구 역할을 한다:

```bash
pnpm dev   # → http://localhost:3000/foundations
```

- **`/foundations/color`** — 모든 semantic 토큰을 색상 swatch + hex 로 시각화 (라이트/다크 토글 가능) + 그것이 참조하는 primitive 스케일
- **`/foundations/typography`** — 27 토큰의 실제 렌더링
- **`/foundations/scale`** — radius · shadow · spacing
- **`/components`** — 부품별 cva variant 시연

`/apply-tokens` 가 빌드 verify 까지 통과한 뒤에도 이 화면들의 시각 검수가 마지막 sanity check.

---

## 관련 문서

- [`docs/design-system.md`](./design-system.md) — 토큰 _값_ SSOT (자동 동기화)
- [`docs/component-variants.md`](./component-variants.md) — 코드 어휘 _호출법_ SSOT (수동 관리)
- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — cross-cutting 규칙
- [`AGENTS.md`](../AGENTS.md) — 레포 진입점 가이드 + Design Token Enforcement 규칙
- `.claude/commands/sync-figma.md` — `/sync-figma` 커맨드 정의
- `.claude/commands/apply-tokens.md` — `/apply-tokens` 커맨드 정의
