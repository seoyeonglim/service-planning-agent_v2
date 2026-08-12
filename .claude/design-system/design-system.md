# Wrtn AX Design System — Figma SSOT

> 이 문서는 `/sync-figma` 커맨드로 Figma BX 스키마를 그대로 박제한 산출물이다.
> 직접 편집하지 말 것. Figma에서 변경 후 `/sync-figma`를 다시 실행한다.
> 코드 어휘(shadcn)로의 매핑은 `/apply-tokens`가 담당한다 — 이 문서가 어휘 번역의 책임을 지지 않는다.

- **Figma File Key**: `hopt0qZUlSeBDJPebenZjy`
- **Design System Node**: `2007:2` ([Figma에서 열기](https://www.figma.com/design/hopt0qZUlSeBDJPebenZjy/?node-id=2007-2))
- **Last Synced**: `2026-07-22T20:55:00Z`
- **Schema**: BX v5 (DP-refined) — 슬래시 경로 시맨틱 + primitive scale 2-tier + alpha 신설
- **적용 대상**: 본 레포(`@wrtn/nextjs-shadcn`)의 `src/app/globals.css` + `src/theme/tokens.ts`

---

## 1. Primitive Scales

### 1.0 Base

| Token   | Hex       |
| ------- | --------- |
| `white` | `#FFFFFF` |
| `black` | `#0A0A0F` |

### 1.1 Luminous Mint (브랜드, main = 500)

| Step | Hex       |
| ---- | --------- |
| 50   | `#E0FFF9` |
| 100  | `#C4FFF2` |
| 200  | `#9EFAE6` |
| 300  | `#77F5DA` |
| 400  | `#50EFD2` |
| 500  | `#09ECC6` |
| 600  | `#08C4A4` |
| 700  | `#079883` |
| 800  | `#056B61` |
| 900  | `#033F3C` |
| 1000 | `#022A2A` |
| 1100 | `#001818` |

### 1.2 Gray (BX Gray + 75 추가)

| Step | Hex       |
| ---- | --------- |
| 50   | `#F5F5FA` |
| 75   | `#EAEAEF` |
| 100  | `#DCDCE1` |
| 200  | `#C8C8CD` |
| 300  | `#B4B4B9` |
| 400  | `#96969B` |
| 500  | `#828287` |
| 600  | `#6E6E73` |
| 700  | `#5A5A5F` |
| 800  | `#46464B` |
| 900  | `#323237` |
| 1000 | `#1E1E23` |
| 1100 | `#0A0A0F` |

### 1.3 Status Primitives (Tailwind 차용, 3 stops → 6 stops 확장)

라이트/다크 모드에서 서로 다른 stop 을 참조한다. semantic 매핑은 2.4절 참조.

**Red — Error**

| Step | Hex       |
| ---- | --------- |
| 100  | `#FECACA` |
| 300  | `#FCA5A5` |
| 400  | `#F87171` |
| 500  | `#EF4444` |
| 700  | `#B91C1C` |
| 900  | `#7F1D1D` |

**Amber — Warning**

| Step | Hex       |
| ---- | --------- |
| 100  | `#FED7AA` |
| 300  | `#FCD34D` |
| 400  | `#FBBF24` |
| 500  | `#F59E0B` |
| 700  | `#B45309` |
| 900  | `#78350F` |

**Green — Success**

| Step | Hex       |
| ---- | --------- |
| 100  | `#BBF7D0` |
| 300  | `#86EFAC` |
| 400  | `#4ADE80` |
| 600  | `#16A34A` |
| 800  | `#166534` |
| 900  | `#14532D` |

**Blue — Info**

| Step | Hex       |
| ---- | --------- |
| 100  | `#BFDBFE` |
| 300  | `#93C5FD` |
| 400  | `#60A5FA` |
| 600  | `#2563EB` |
| 800  | `#1E40AF` |
| 900  | `#1E3A8A` |

### 1.4 Alpha (신설 — DP 인라인 rgba 흡수)

각 패밀리 3단계. Figma 상에는 % 라벨만 표시되고 base 색은 이름에서 파생.

| Token             | Value                       | Base                |
| ----------------- | --------------------------- | ------------------- |
| `alpha/black/05`  | `rgba(10, 10, 15, 0.05)`    | `black` `#0A0A0F`   |
| `alpha/black/10`  | `rgba(10, 10, 15, 0.10)`    | `black` `#0A0A0F`   |
| `alpha/black/40`  | `rgba(10, 10, 15, 0.40)`    | `black` `#0A0A0F`   |
| `alpha/white/10`  | `rgba(255, 255, 255, 0.10)` | `white` `#FFFFFF`   |
| `alpha/white/16`  | `rgba(255, 255, 255, 0.16)` | `white` `#FFFFFF`   |
| `alpha/white/45`  | `rgba(255, 255, 255, 0.45)` | `white` `#FFFFFF`   |
| `alpha/mint/10`   | `rgba(9, 236, 198, 0.10)`   | `mint/500` `#09ECC6` |
| `alpha/mint/20`   | `rgba(9, 236, 198, 0.20)`   | `mint/500` `#09ECC6` |
| `alpha/mint/40`   | `rgba(9, 236, 198, 0.40)`   | `mint/500` `#09ECC6` |

---

## 2. Semantic Color Tokens

> 모든 토큰은 슬래시 경로(`category/role[/variant]`) 그대로 박제. light/dark 두 모드 분리.
> **primitive 를 직접 쓰지 말고 semantic 만 사용한다** — 근거는 `docs/design-playbook.md` 1.1 절.

### 2.1 Surface

| Token                    | Light                | Dark                  |
| ------------------------ | -------------------- | --------------------- |
| `surface/elevated`       | `#FFFFFF` (white)    | `#1E1E23` (gray/1000) |
| `surface/secondary`      | `#F5F5FA` (gray/50)  | `#323237` (gray/900)  |
| `surface/tertiary`       | `#EAEAEF` (gray/75)  | `#46464B` (gray/800)  |
| `surface/sunken`         | `#F5F5FA` (gray/50)  | `#0A0A0F` (gray/1100) |
| `surface/disabled`       | `#DCDCE1` (gray/100) | `#46464B` (gray/800)  |
| `surface/elevated_invert`| `#1E1E23` (gray/1000)| `#FFFFFF` (white)     |

### 2.2 Text

| Token           | Light                 | Dark                 |
| --------------- | --------------------- | -------------------- |
| `text/primary`  | `#1E1E23` (gray/1000) | `#F5F5FA` (gray/50)  |
| `text/secondary`| `#6E6E73` (gray/600)  | `#96969B` (gray/400) |
| `text/tertiary` | `#96969B` (gray/400)  | `#828287` (gray/500) |
| `text/disabled` | `#B4B4B9` (gray/300)  | `#6E6E73` (gray/600) |
| `text/white`    | `#FFFFFF`             | `#FFFFFF`            |
| `text/invert`   | `#FFFFFF`             | `#1E1E23` (gray/1000)|
| `text/black`    | `#0A0A0F` (black)     | `#0A0A0F` (black)    |

### 2.3 Icon (신설 패밀리)

| Token           | Light                 | Dark                 |
| --------------- | --------------------- | -------------------- |
| `icon/primary`  | `#1E1E23` (gray/1000) | `#F5F5FA` (gray/50)  |
| `icon/secondary`| `#6E6E73` (gray/600)  | `#96969B` (gray/400) |
| `icon/tertiary` | `#96969B` (gray/400)  | `#828287` (gray/500) |
| `icon/disabled` | `#B4B4B9` (gray/300)  | `#6E6E73` (gray/600) |
| `icon/invert`   | `#FFFFFF` (white)     | `#1E1E23` (gray/1000)|
| `icon/black`    | `#0A0A0F` (black)     | `#0A0A0F` (black)    |

### 2.4 Status (subtle / default / emphasis 3단계)

| Token                    | Light                 | Dark                  |
| ------------------------ | --------------------- | --------------------- |
| `status/error/subtle`    | `#FECACA` (red/100)   | `#7F1D1D` (red/900)   |
| `status/error/default`   | `#EF4444` (red/500)   | `#F87171` (red/400)   |
| `status/error/emphasis`  | `#B91C1C` (red/700)   | `#FCA5A5` (red/300)   |
| `status/warning/subtle`  | `#FED7AA` (amber/100) | `#78350F` (amber/900) |
| `status/warning/default` | `#F59E0B` (amber/500) | `#FBBF24` (amber/400) |
| `status/warning/emphasis`| `#B45309` (amber/700) | `#FCD34D` (amber/300) |
| `status/success/subtle`  | `#BBF7D0` (green/100) | `#14532D` (green/900) |
| `status/success/default` | `#16A34A` (green/600) | `#4ADE80` (green/400) |
| `status/success/emphasis`| `#166534` (green/800) | `#86EFAC` (green/300) |
| `status/info/subtle`     | `#BFDBFE` (blue/100)  | `#1E3A8A` (blue/900)  |
| `status/info/default`    | `#2563EB` (blue/600)  | `#60A5FA` (blue/400)  |
| `status/info/emphasis`   | `#1E40AF` (blue/800)  | `#93C5FD` (blue/300)  |

### 2.5 Outline (3단계 신설)

| Token             | Light                | Dark                 |
| ----------------- | -------------------- | -------------------- |
| `outline/subtle`  | `#EAEAEF` (gray/75)  | `#323237` (gray/900) |
| `outline/default` | `#DCDCE1` (gray/100) | `#46464B` (gray/800) |
| `outline/strong`  | `#C8C8CD` (gray/200) | `#5A5A5F` (gray/700) |

### 2.6 Accent (신설 — text / bg 분리)

| Token         | Light                | Dark                  |
| ------------- | -------------------- | --------------------- |
| `accent/solid`  | `#079883` (mint/700) | `#77F5DA` (mint/300)  |
| `accent/subtle` | `#E0FFF9` (mint/50)  | `#022A2A` (mint/1000) |

### 2.7 Background

| Token                | Light             | Dark                  |
| -------------------- | ----------------- | --------------------- |
| `background/primary` | `#FFFFFF` (white) | `#0A0A0F` (gray/1100) |

### 2.8 Primary (브랜드 — 라이트/다크 통일)

| Token          | Light                | Dark                 |
| -------------- | -------------------- | -------------------- |
| `primary/main` | `#09ECC6` (mint/500) | `#09ECC6` (mint/500) |

---

## 3. Typography (Aurora-Lean v4.1)

| Token         | Weight   | Size | Line-height | Letter-spacing |
| ------------- | -------- | ---- | ----------- | -------------- |
| `header/40`   | Bold     | 40px | 120%        | (값 없음)      |
| `header/32`   | Bold     | 32px | 120%        | (값 없음)      |
| `header/28`   | Bold     | 28px | 120%        | (값 없음)      |
| `title/24`    | Bold     | 24px | 150%        | (값 없음)      |
| `title/20`    | Bold     | 20px | 150%        | (값 없음)      |
| `title/18`    | Bold     | 18px | 150%        | (값 없음)      |
| `title/16`    | Bold     | 16px | 150%        | (값 없음)      |
| `title/14`    | Bold     | 14px | 140%        | (값 없음)      |
| `subtitle/24` | SemiBold | 24px | 150%        | (값 없음)      |
| `subtitle/20` | SemiBold | 20px | 150%        | (값 없음)      |
| `subtitle/18` | SemiBold | 18px | 150%        | (값 없음)      |
| `subtitle/16` | SemiBold | 16px | 150%        | (값 없음)      |
| `subtitle/14` | SemiBold | 14px | 140%        | (값 없음)      |
| `body/24`     | Medium   | 24px | 150%        | (값 없음)      |
| `body/20`     | Medium   | 20px | 150%        | (값 없음)      |
| `body/18`     | Medium   | 18px | 150%        | (값 없음)      |
| `body/16`     | Medium   | 16px | 150%        | (값 없음)      |
| `body/14`     | Medium   | 14px | 140%        | (값 없음)      |
| `label/20`    | Bold     | 20px | 100%        | (값 없음)      |
| `label/16`    | Bold     | 16px | 100%        | (값 없음)      |
| `label/14`    | SemiBold | 14px | 100%        | (값 없음)      |
| `label/12`    | Medium   | 12px | 100%        | (값 없음)      |
| `text/20`     | Regular  | 20px | 150%        | (값 없음)      |
| `text/18`     | Regular  | 18px | 150%        | (값 없음)      |
| `text/16`     | Regular  | 16px | 150%        | (값 없음)      |
| `text/14`     | Regular  | 14px | 140%        | (값 없음)      |
| `text/12`     | Regular  | 12px | 150%        | (값 없음)      |

> `text/*`는 Plain Text 본문용 (Regular weight 전용). header/title/subtitle/body/label 22개 + text 5개 = 총 27 tokens.

**Font family**: `Pretendard Variable` (Bold / SemiBold / Medium / Regular 4 weights 사용 중)

---

## 4. Radius

| Token         | Value      |
| ------------- | ---------- |
| `radius/sm`   | 4px        |
| `radius/md`   | 8px        |
| `radius/lg`   | 12px       |
| `radius/xl`   | 16px       |
| `radius/2xl`  | 24px       |
| `radius/full` | 9999px (∞) |

---

## 5. Shadow

| Token               | Value                                                                      | Note                            |
| ------------------- | -------------------------------------------------------------------------- | ------------------------------- |
| `shadow/sm`         | `0 1px 2px -1px rgba(0, 0, 0, 0.10), 0 1px 3px 0 rgba(0, 0, 0, 0.10)`      | 카드 기본                       |
| `shadow/md`         | `0 2px 4px -2px rgba(0, 0, 0, 0.10), 0 4px 6px -1px rgba(0, 0, 0, 0.10)`   | 호버 · 드롭다운                 |
| `shadow/lg`         | `0 4px 6px -4px rgba(0, 0, 0, 0.10), 0 10px 15px -3px rgba(0, 0, 0, 0.10)` | 모달 · 팝오버                   |
| `shadow/brand-glow` | (값 없음 — Figma에서 hidden 상태, 동기화 노트 참조)                        | 활성 · 강조 (mint 700/500 기반) |

> **Shadow Card 컨텍스트**: Figma의 카드 프리뷰는 `border-radius: 8px` + `border: 1px solid #EAEAEF` (`outline/default` light) + `background: #FFFFFF` (`surface/elevated` light) 위에 box-shadow가 적용된 형태로 시각화돼있다. 위 표의 값은 box-shadow 부분만 박제. radius/border/background는 각각의 토큰을 조합해 사용한다.

---

## 6. Spacing

| Token       | Value |
| ----------- | ----- |
| `space/0`   | 0px   |
| `space/0.5` | 2px   |
| `space/1`   | 4px   |
| `space/1.5` | 6px   |
| `space/2`   | 8px   |
| `space/3`   | 12px  |
| `space/4`   | 16px  |
| `space/6`   | 24px  |
| `space/8`   | 32px  |
| `space/12`  | 48px  |
| `space/16`  | 64px  |

---

## 동기화 노트

### 2026-07-22 · v5 재동기화 (DP-refined draft, 컬러 전용)

Figma 파일 이동: `F9DCw53UeJLEz1HPtuZSb1/141:51` (v4) → `hopt0qZUlSeBDJPebenZjy/2007:2` (v5). **이번 sync 는 컬러 섹션(1·2절)에만 적용**하고 typography/radius/shadow/spacing 은 v4 값을 그대로 유지했다.

**v5 리팩터 근거** — v4 semantic 이 다크모드에서 커버리지 부족해 dana 가 실제 랜딩 작업 중 primitive 를 직접 꺼내 써야 했다. v5 는 dark stop 확장 + sunken/outline 3단 + icon 패밀리 + alpha 신설로 그 갭을 메웠고, 실증 실험(Figma `2084-1006` 라이트 / `2084-235` 다크) 에서 semantic 만으로 두 모드 모두 정상 표현 확인. → `docs/design-playbook.md` 1.1 절에 primitive 직접 사용 금지 RULE 추가됨.

**Breaking changes — `/apply-tokens` 이전 반드시 코드 마이그레이션 필요**:

| 종류 | v4 | v5 | 영향 |
| --- | --- | --- | --- |
| RENAME | `status/*/light` | `status/*/subtle` | Tailwind class, tokens.ts alias |
| RENAME | `status/*/dark` | `status/*/emphasis` | 동상 |
| RENAME | `status/*/default` | `status/*/default` | 유지 (구조만 정리) |
| RENAME | `surface/raised` | `surface/tertiary` | raised는 hover 명명과 충돌 |
| MERGE | `surface/primary` + `surface/elevated` | `surface/elevated` | shadcn `--background`/`--card` 매핑 재점검 |
| MERGE | `surface/primary/invert` + `surface/elevated/invert` + `text/invert` | `surface/elevated_invert` + `text/invert` | |
| EDIT | `primary/main` light = `#079883` (mint/700) | `#09ECC6` (mint/500) | **라이트 primary 톤 크게 밝아짐 — WCAG 대비 재검토** |
| RENAME | `alpha/90` | `alpha/white/10` | |
| DROP | `primary/dark`, `primary/foreground` | — | 사용처 grep 후 semantic 재매핑 |
| DROP | `surface/hover`, `surface/overlay` | — | 컴포넌트 단에서 `alpha/*` 로 처리 |
| DROP | `background/secondary` | — | |
| DROP | `outline/focus` | — | 컴포넌트 단 + `primary/main` |
| DROP | `surface/white` | — | (v4 sync note 4 참조) Switch 컴포넌트가 `var(--surface/white)` 사용 중 → `text/white` 또는 `background/primary` 로 대체 필요 |
| DROP | `error/base`/`success/base`/`warning/base`/`info/base` | — | `status/*/subtle` 로 흡수 (rename + 계열 재구조화) |
| ADD | `surface/sunken` | | elevated 컨테이너 내부용 |
| ADD | `outline/subtle` | | outline 3단화 |
| ADD | `icon/*` 6종 | | text 와 별도로 아이콘 컬러 명시 |
| ADD | `text/black`, `icon/black` | | 모드 무관 흑색 고정 |
| ADD | `accent/solid`, `accent/subtle` | | 마케팅 하이라이트용 mint tint (Figma canonical: solid=텍스트 강조, subtle=chip 배경) |
| ADD | `alpha/black/05·10·40`, `alpha/white/10·16·45`, `alpha/mint/10·20·40` | | DP 인라인 rgba 47회 흡수 |
| ADD | `space/0` | | |
| ADD | Primitive Status 3 → 6 stops | | 모드별 다른 stop 사용 |

**Alpha base 색 미확정** — Figma 카드에 % 라벨만 표시돼 있고 hex 값은 노출되지 않는다. 본 문서는 이름에서 파생한 값(black=`#0A0A0F`, white=`#FFFFFF`, mint=`mint/500 #09ECC6`)을 잠정 표기했다. `/apply-tokens` 이전에 dana 컨펌 필요.

**Shadow 확장 예정** — v5 changelog 에 shadow xs/sm/md/lg + brand-glow sm/md/lg 확장 항목이 있으나 이번 sync 범위(컬러 전용)에서는 반영하지 않음. 별도 shadow sync 시점에 처리.

### 이전 노트 (v4 시점)

이번 동기화에서 누락되어 **수동 보정 또는 재추출이 필요한 항목**:

1. **Typography letter-spacing** — 메타데이터에 명시 없음. Aurora-Lean v4.1 디자인 의도에 따라 별도 정의 필요.
2. **`shadow/brand-glow`는 Figma에서 hidden 상태** — frame `164:140`의 자식 `166:3`이 `visible=false`로 정의돼있어 시각/코드 컨텍스트 모두에서 빠진다. effects 값도 hidden 상태라 추출되지 않음. 사용자가 "처음 본다"고 한 이유. 활성·강조(mint 700/500) 용도로 기획됐으나 미공개 상태인지, 폐기 예정인지 디자이너 컨펌 필요. 컨펌 후 (a) 값 박제 또는 (b) 본문 표에서 영구 제거.
3. **shadcn 어휘 매핑은 `/apply-tokens`에서 처리** — 위 BX 슬래시 토큰을 `--primary`, `--background` 등 shadcn CSS 변수로 매핑하는 책임은 `/apply-tokens` 커맨드가 가진다. 이 문서는 어떤 매핑도 가정하지 않는다.
4. **신규 토큰 추가 (2026-04-29 재동기화)** — Figma BX frame에 `surface/white`, `text/white` 두 토큰이 추가됨. 둘 다 light/dark 모두 `#FFFFFF` 고정. 모드 무관 흰색 고정용. Switch 컴포넌트가 이미 `var(--surface/white)`를 사용 중이었으므로 이 추가는 컴포넌트 사용처와 일치한다. **v5 update**: `surface/white` 는 v5 에서 drop 됨 → Switch 재매핑 필요.
5. **Primitive 스케일 1100 스텝 추가 (2026-05-06 재동기화)** — Figma BX frame에 Luminous Mint 1100 (`#001818`)과 Gray 1100 (`#0A0A0F`) 두 단계가 추가됨. 둘 다 기존 1000 (Mint `#022A2A`, Gray `#1E1E23`) 보다 어두운 극단 다크 톤. **v5 update**: 1100 이 semantic 에서 실제로 사용되기 시작 — `background/primary` dark = `gray/1100 #0A0A0F`, `surface/sunken` dark = `gray/1100`.
