# Component Variants & Token Utility Cheatsheet

> Wrtn AX 디자인 시스템(`docs/design-system.md`)이 shadcn/ui 코드에서 어떻게 노출되는지를
> 정리한 단일 SSOT 문서. **적용 대상**: 본 레포(`@wrtn/nextjs-shadcn`).

색상/스타일을 사용하는 방법은 두 갈래다:

1. **컴포넌트 cva variant** — `<Button variant="destructive">` 처럼 미리 조합된 props 로 호출.
2. **Tailwind utility 클래스** — `bg-status-success-subtle text-status-success-emphasis` 같은 v5 canonical semantic 클래스를 직접 사용.

두 방식 모두 토큰만 사용한다 (raw hex / Tailwind primitive 클래스 / arbitrary value / shadcn alias 클래스 금지 — 자세한 enforcement 규칙은 `AGENTS.md` "Design Token Enforcement" 섹션과 `docs/design-playbook.md` 1.1 참고).

---

## 0. Figma 정의 컴포넌트 카탈로그 (계층 2)

Figma 에 정의된 모든 DS 컴포넌트는 `src/components/ui/` 한 폴더에 모여 있다. `docs/workflow.md` 의 "디자인 시스템 적용 우선순위" 의 계층 2 에 해당하며, **있으면 무조건 우선 사용**.

> **폴더 정책**: shadcn 의 표준은 `components/ui/` 한 폴더에 모든 컴포넌트(primitive + composed) 를 담는 것이고, 우리도 그 컨벤션을 따른다. shadcn Blocks (https://ui.shadcn.com/blocks) 개념도 코드 폴더 분리 없이 동일하게 `ui/` 에 들어간다.

### 0.1 단일 부품 — Figma `177:1671`

PoC essential 최소 셋으로 디자이너가 확정한 컴포넌트 패밀리.

| #   | 컴포넌트 패밀리 | 코드 구현 (`src/components/ui/`) |
| --- | --------------- | -------------------------------- |
| 1   | **Button**      | `button.tsx` ✅                  |
| 2   | **Input**       | `input.tsx` ✅                   |
| 3   | **Card**        | `card.tsx` ✅                    |
| 4   | **Badge**       | `badge.tsx` ✅                   |
| 5   | **Tabs**        | `tabs.tsx` ✅                    |
| 6   | **Switch**      | `switch.tsx` ✅                  |
| 7   | **Dialog**      | `dialog.tsx` ✅                  |
| 8   | **Select**      | `select.tsx` ✅                  |
| 9   | **Checkbox**    | `checkbox.tsx` ✅                |

> **참고 — Figma 에는 없지만 코드에 있는 부수 컴포넌트**: `alert.tsx`, `label.tsx`, `separator.tsx`, `textarea.tsx`. 단순 utility 라 별도 디자인 안 함. 사용 가능하나 Figma SSOT 가 아니므로 시각 변경 시 디자이너 컨펌 필요.

각 컴포넌트의 variant 호출법은 1번 섹션 참조. variant 상세 (spec, anatomy, padding 등) 은 추후 별도 작업으로 보강 예정 (`/sync-figma-components` 가능성).

### 0.2 조합 컴포넌트 — Figma `219:5779` \_Blocks/\*

ui 부품을 조합한 도메인 컴포넌트. PoC 에서 화면 단위로 바로 import 해 사용. (코드 위치는 `0.1` 과 동일하게 `src/components/ui/`.)

| #   | 컴포넌트                | 코드 구현 (`src/components/ui/`) | Figma node                                 |
| --- | ----------------------- | -------------------------------- | ------------------------------------------ |
| 1   | **Nav**                 | `nav.tsx` ✅                     | `219:5808` (desktop) / `219:5979` (mobile) |
| 2   | **Nav Item**            | `nav-item.tsx` ✅                | `219:5799` (v1) / `219:5972` (v2)          |
| 3   | **Menu Item**           | `menu-item.tsx` ✅               | `219:5876` (base)                          |
| 4   | **Menu / Desktop**      | (menu-item 조합)                 | `219:6131`                                 |
| 5   | **Menu / Mobile**       | (menu-item 조합)                 | `219:5921`                                 |
| 6   | **Sidebar**             | `sidebar.tsx` ✅                 | `219:6095`                                 |
| 7   | **Sidebar Item**        | `sidebar-item.tsx` ✅            | `219:6071`                                 |
| 8   | **Notification Item**   | `notification-item.tsx` ✅       | `194:185`                                  |
| 9   | **Notification Number** | `notification-number.tsx` ✅     | (nav/sidebar 내 사용)                      |
| 10  | **Statistic Card**      | `statistic-card.tsx` ✅          | `219:5779` 자식                            |
| 11  | **Text Editor**         | `text-editor.tsx` ✅             | `219:6032`                                 |
| 12  | **Uploader**            | `uploader.tsx` ✅                | `219:5779` 자식                            |
| 13  | **User Item**           | `user-item.tsx` ✅               | `219:5779` 자식                            |
| 14  | **Legend**              | `legend.tsx` ✅                  | `219:5779` 자식                            |

> 조합 컴포넌트는 cva variant 가 아닌 props 기반이라 1번 섹션 (variant 표) 에는 포함되지 않는다. 사용법은 playground 의 `_Blocks Tier 1` 섹션 (Figma `219:5779`) 데모 참조.

---

## 1. 컴포넌트 cva variant

shadcn 컴포넌트의 `variant` prop 으로 사용 가능한 값.

### Button (`src/components/ui/button.tsx`)

| Variant       | 의도                     | 토큰 매핑 (v5 canonical)                                  |
| ------------- | ------------------------ | --------------------------------------------------------- |
| `default`     | 1차 액션                 | `bg-primary-main text-text-black`                         |
| `outline`     | 보조 액션 (테두리만)     | `border-outline-default bg-transparent text-text-primary` |
| `secondary`   | 보조 액션 (채워진 회색)  | `bg-surface-tertiary text-text-primary`                   |
| `ghost`       | 최소 강조 (호버 시 배경) | `text-text-primary hover:bg-surface-tertiary`             |
| `destructive` | 파괴적 액션 (삭제 등)    | `bg-status-error-default text-text-black`                 |
| `link`        | 인라인 링크              | `text-primary-main underline-offset-4`                    |

Sizes: `default`, `sm`, `lg`, `icon`.

> **v5 에서 Button `accent` variant 삭제** (2026-07-22). accent 강조가 필요하면
> `<Badge variant='accent'>` 또는 `bg-accent-subtle text-accent-solid` utility 를 사용한다.

### Badge (`src/components/ui/badge.tsx`)

| Variant       | 의도                        | 토큰 매핑 (v5 canonical)                                |
| ------------- | --------------------------- | ------------------------------------------------------- |
| `default`     | 기본 강조                   | `bg-primary-main text-text-black`                       |
| `accent`      | 브랜드 accent 강조 (커스텀) | `bg-accent-subtle text-accent-solid`                    |
| `secondary`   | 보조 라벨                   | `bg-surface-secondary text-text-primary`                |
| `outline`     | 테두리 라벨                 | `border-outline-default text-text-primary`              |
| `success`     | 성공/완료 (커스텀)          | `bg-status-success-subtle text-status-success-emphasis` |
| `warning`     | 경고/주의 (커스텀)          | `bg-status-warning-subtle text-status-warning-emphasis` |
| `destructive` | 오류/위험                   | `bg-status-error-default text-text-black`               |

### Alert (`src/components/ui/alert.tsx`)

| Variant       | 의도               | 토큰 매핑 (v5 canonical)                                                              |
| ------------- | ------------------ | ------------------------------------------------------------------------------------- |
| `default`     | 일반 알림          | `bg-surface-elevated border-outline-default text-text-primary`                        |
| `success`     | 성공 알림 (커스텀) | `border-status-success-default bg-status-success-subtle text-status-success-emphasis` |
| `warning`     | 경고 알림 (커스텀) | `border-status-warning-default bg-status-warning-subtle text-status-warning-emphasis` |
| `destructive` | 오류 알림          | `border-status-error-default bg-status-error-subtle text-status-error-emphasis`       |

> 새 커스텀 variant 를 추가할 때는 (1) 디자인 토큰만 사용, (2) 위 표에 항목 추가, (3) `AGENTS.md`
> 의 "shadcn/ui 컴포넌트 커스터마이징 정책" 표도 동기화.

### Composite 컴포넌트 (cva variant 없음 — 서브컴포넌트 조합)

Dialog / Select / Checkbox 는 단일 cva variant 가 아닌 서브컴포넌트 조합으로 사용한다.

#### Dialog (`src/components/ui/dialog.tsx`)

| 서브컴포넌트        | 역할                                  |
| ------------------- | ------------------------------------- |
| `Dialog`            | 루트 컨테이너                         |
| `DialogTrigger`     | 다이얼로그 여는 트리거                |
| `DialogContent`     | 모달 본문 (자동으로 X 닫기 버튼 포함) |
| `DialogHeader`      | 제목/설명 wrapper                     |
| `DialogTitle`       | 제목 (text-title-18)                  |
| `DialogDescription` | 부연 설명 (text-body-14, muted)       |
| `DialogFooter`      | 액션 버튼 영역                        |
| `DialogClose`       | 닫기 트리거 (커스텀)                  |

사용 예: `<Dialog><DialogTrigger>...</DialogTrigger><DialogContent><DialogHeader><DialogTitle>...</DialogTitle></DialogHeader></DialogContent></Dialog>`

#### Select (`src/components/ui/select.tsx`)

| 서브컴포넌트      | 역할                    |
| ----------------- | ----------------------- |
| `Select`          | 루트                    |
| `SelectTrigger`   | 트리거 (drop-down 버튼) |
| `SelectValue`     | 현재 선택값 표시        |
| `SelectContent`   | 옵션 목록 portal        |
| `SelectGroup`     | 옵션 그룹               |
| `SelectLabel`     | 그룹 라벨               |
| `SelectItem`      | 개별 옵션               |
| `SelectSeparator` | 옵션 구분선             |

#### Checkbox (`src/components/ui/checkbox.tsx`)

단일 컴포넌트. props: `checked`, `onCheckedChange`, `disabled`. shadcn 표준 Radix wrapping. 체크 시 `bg-primary-main` 적용.

---

## 2. Tailwind utility 클래스

`globals.css` 의 `@theme inline` 블록에 정의된 모든 색상/타이포 토큰은 Tailwind utility 로 자동 노출된다.
shadcn variant 로 표현 안 되는 케이스(혹은 새 컴포넌트 작성 시)는 아래 utility 를 직접 사용한다.

> **이름 정책 (v5)**: 컴포넌트 / 화면 코드는 **v5 canonical semantic 클래스만** 사용한다
> (`bg-surface-elevated`, `text-text-primary`, `border-outline-default`, `bg-primary-main` 등).
> shadcn alias (`bg-background`, `text-foreground`, `border-border`, `bg-primary` 등) 와
> v4 compat alias (`bg-surface-primary`, `text-text-primary-invert`, `bg-success-soft` 등) 는
> `globals.css` 호환 층으로만 남아 있고 새 코드에서 금지한다 (`docs/design-playbook.md` 1.1 RULE).
> 기존 코드의 alias 사용은 `check:design` 이 WARN 으로 추적하는 마이그레이션 백로그다.

### Surface / Background

| Family         | 사용 가능 클래스                                                                       |
| -------------- | -------------------------------------------------------------------------------------- |
| `surface/*`    | `bg-surface-{elevated,secondary,tertiary,sunken,disabled,hover,white}`                 |
|                | `bg-surface-elevated-invert` (반전 표면)                                               |
|                | (v4 compat: `bg-surface-primary`, `bg-surface-primary-invert` — 신규 코드 사용 금지)   |
| `background/*` | `bg-background-{primary,secondary}` — **페이지 캔버스 배경 전용** (playbook 1.1 RULE). |
|                | 카드/탭/dialog/panel 표면에는 `bg-surface-*` 를 쓴다.                                  |

### Text / Icon

| Family   | 사용 가능 클래스                                                                          |
| -------- | ----------------------------------------------------------------------------------------- |
| `text/*` | `text-text-{primary,secondary,tertiary,disabled,white,invert,black}`                      |
|          | (v4 compat: `text-text-primary-invert` = `invert` — 신규 코드 사용 금지)                  |
| `icon/*` | `text-icon-{primary,secondary,tertiary,disabled,invert,black}` (v5 신설 — svg 아이콘 색) |

### Outline / Border

| Family      | 사용 가능 클래스                                              |
| ----------- | ------------------------------------------------------------- |
| `outline/*` | `border-outline-{subtle,default,strong}` (subtle: v5 신설)    |

### Primary / Accent (브랜드)

| Token                | 사용 가능 클래스                                                                   |
| -------------------- | ---------------------------------------------------------------------------------- |
| `primary/main`       | `bg-primary-main`, `text-primary-main`, `border-primary-main`, `ring-primary-main` |
| `primary/light`      | `text-primary-light`, `bg-primary-light`                                           |
| `primary/dark`       | `text-primary-dark`, `bg-primary-dark`                                             |
| `accent/*`           | `bg-accent-solid`, `text-accent-solid`, `bg-accent-subtle` (v5 신설)               |

> **v5 에서 `accent/solid`·`accent/subtle` 이 정식 분리됐다.** primary fill 위 텍스트는
> `text-text-black` 을 쓴다 (`text-primary-foreground` 는 shadcn alias — 금지, playbook 1.1).
> shadcn alias `bg-accent`(= `primary/main`)·`bg-accent-soft` 를 canonical 로 재배선하는
> 작업은 시각 변화가 따르므로 마이그레이션 백로그로 남긴다 (dana 컨펌 필요).

### Status (error / success / warning / info)

v5 canonical — `status/{family}/{subtle|default|emphasis}` 3단계:

| Family    | 사용 가능 클래스 (`bg-` 외 `text-`, `border-` 동일 적용)  |
| --------- | ---------------------------------------------------------- |
| `error`   | `bg-status-error-{subtle,default,emphasis}`                |
| `warning` | `bg-status-warning-{subtle,default,emphasis}`              |
| `success` | `bg-status-success-{subtle,default,emphasis}`              |
| `info`    | `bg-status-info-{subtle,default,emphasis}`                 |

각 단계의 의미:

- **`subtle`** — 옅은 배경 (배지 / 알림 표면). v4 의 `base`.
- **`default`** — 표준 강조 (아이콘 / 테두리 / 채움).
- **`emphasis`** — 다크모드에서는 더 밝은, 라이트모드에서는 더 진한 강조 텍스트.
- status default fill 위 고대비 텍스트는 `text-text-black` (dark 계열 fill) 등 text 토큰으로 직접 지정한다.

> **v4 compat alias** (`bg-destructive`, `bg-success-soft`, `text-warning-emphasis`,
> `bg-error-base` 등) 는 호환 층에만 남아 있고 신규 코드 사용 금지 — `check:design` 이
> WARN 으로 추적하는 마이그레이션 백로그다.

### Primitive scale (v5 부터 직접 사용 금지)

`mint-*`, `gray-*`, `red-*`, `amber-*`, `green-*`, `blue-*`, `alpha-*` primitive 는
`globals.css` / `tokens.ts` 안에서 semantic 이 참조하는 원천으로만 존재한다.
컴포넌트 / 화면 코드에서 직접 사용하지 않는다 (`docs/design-playbook.md` 1.1 RULE).
필요한 semantic 이 없으면 primitive 로 때우지 말고 dana 에게 문의해
`design-system.md` 에 semantic 을 먼저 추가한다.

---

## 3. Typography

`docs/design-system.md` 3번 섹션 의 27 토큰을 모두 utility 로 노출. font-size + line-height + font-weight 가
한 클래스로 적용된다.

| Family   | 클래스                                                            | weight               |
| -------- | ----------------------------------------------------------------- | -------------------- |
| header   | `text-header-{40,32,28}`                                          | Bold                 |
| title    | `text-title-{24,20,18,16,14}`                                     | Bold                 |
| subtitle | `text-subtitle-{24,20,18,16,14}`                                  | SemiBold             |
| body     | `text-body-{24,20,18,16,14}`                                      | Medium               |
| label    | `text-label-{20,16,14,12}` (14: SemiBold, 12: Medium, 그 외 Bold) | Bold/SemiBold/Medium |
| plain    | `text-plain-{20,18,16,14,12}` (DS의 `text/*`)                     | Regular              |

> `plain` 은 namespace 충돌 회피 결정 — DS 마크다운의 `text/14` 가 코드에서는 `text-plain-14`.
> `text-sm`, `text-lg`, `text-xl` 같은 Tailwind 기본 utility 는 사용 금지 (AGENTS.md 4번 섹션).

helper 가 필요하면 `import { typography } from '@/lib/typography'` — 27 키를 camelCase 로 노출 (`typography.header40`, `typography.subtitle16`, ...).

---

## 4. Radius / Shadow / Spacing

| 카테고리 | 클래스                                                     | 값 (`docs/design-system.md` 기준) |
| -------- | ---------------------------------------------------------- | --------------------------------- |
| radius   | `rounded-{sm,md,lg,xl,2xl,full}`                           | 4 / 8 / 12 / 16 / 24 / 9999 px    |
| shadow   | `shadow-{sm,md,lg}`                                        | DS 5번 섹션 박제 값               |
| spacing  | Tailwind 기본 4px 그리드 (`p-{0.5,1,1.5,2,3,4,6,8,12,16}`) | DS 6번 섹션 와 자동 정합          |

---

## 5. 검증 / Playground

`/playground` 페이지에서 모든 variant 와 토큰을 시각적으로 확인할 수 있다:

```bash
pnpm dev   # → http://localhost:3000/playground
```

playground 의 "토큰" 탭에는 현재 모드의 모든 semantic 토큰이 색상 swatch 와 함께 노출되며,
"Buttons" / "Badges" / "Alerts" 섹션에서 cva variant 가 모두 시연된다.

---

## 6. 새 토큰 / 새 variant 추가 절차

1. `docs/design-system.md` 에 토큰 추가 (가능하면 `/sync-figma` 로).
2. `globals.css` 의 semantic 블록 + `@theme inline` 매핑 동기화.
3. `theme/tokens.ts` 의 TS 미러 동기화 (라이트/다크 양쪽).
4. variant 추가 시 해당 컴포넌트의 cva 와 본 문서 1번 섹션 표 갱신.
5. `pnpm verify` (lint + format:check + check:design + build) 로 검증.

---

## 참고

- 디자인 토큰 SSOT: [`docs/design-system.md`](./design-system.md)
- 토큰 사용 강제 규칙: [`AGENTS.md`](../AGENTS.md) "Design Token Enforcement" 섹션
- cross-cutting 아키텍처 규칙: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
