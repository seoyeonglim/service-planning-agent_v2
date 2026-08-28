# Design Playbook

> ⤳ vendored from ax-design-system @ 9a6e7c5 · doc-sha 70c6a6c2e41e · 0~9 섹션 수정 금지 · 정본 변경 시 재동기화
> 원격은 `git@github.wrtn.club:wrtn-tech/ax-design-system.git` 브랜치 `develop`. 이 레포에서의 보관 위치는 `docs/` 가 아니라 `.claude/design-system/` 이다 — 이 레포의 `docs/` 는 고객 산출물 유출 방지를 위해 통째로 git 추적 제외이기 때문. 사유는 `design-playbook.md` "10. 프로젝트별 슬롯" 참조.

> ⤳ vendor: required — 공통 기준선이라 유형과 무관하게 모든 소비 레포가 가져간다. 0~9 섹션 수정 금지 · 프로젝트 편차는 "10. 프로젝트별 슬롯" 에만.

**대상:** Claude (PoC 제작 시 컨텍스트로 주입)
**역할:** ax-design-system 기반 PoC들이 공통으로 따르는 **레이아웃·구성·인터랙션 기준선**. `design-system.md`(토큰 값)와 짝을 이루는 "그 토큰을 화면에 어떻게 적용하나" 문서.
**토큰과의 관계:** 색·타이포·radius·shadow·spacing의 *값*은 이 문서가 정하지 않는다. SSOT는 `docs/design-system.md` + `tokens.ts`. PoC는 그 토큰을 **상속**해서 쓴다. 이 문서는 **"상속받은 토큰을 배치·구성·반응시키는 법" + "템플릿 토큰에서 이탈하지 말 것"**만 다룬다.
**버전:** v0.5-draft · 2026-05-29
**적용법:** 이 파일을 PoC 레포 루트(또는 docs)에 두고 `CLAUDE.md`에서 `@design-playbook.md`로 참조. 프로젝트 고유 사항은 "10. 프로젝트별 슬롯"에 덧붙인다.

> ⚠️ **잠정 표시**: 수치 옆 `[제안]`은 기존 PoC들의 drift(사이드바 288 vs 400 등)를 표준 기준으로 모은 값. **그대로 써도 되며 승인을 기다릴 필요는 없다.** 반례가 나오면 사유와 함께 PR 로 갱신한다.


---

## 0. 강제력 어휘 + craft 철학

- **RULE** — 반드시. 어기면 안 됨. (접근성·인터랙션·토큰 이탈 금지처럼 "어디서나 참")
- **PREFER** — 권장 기본값. 화면 단위로 보정 가능하며, 보정했으면 사유를 PR 에 남긴다.
- **AVOID** — 하지 말 것.

> 이 문서는 **구조·인터랙션·토큰 사용은 RULE, 치수·비주얼 기본값은 PREFER**다. "동작하는 방식"은 고정, "보이는 값"은 열어둔다.

> 🎨 **craft 철학:** 이 문서는 가드레일이지 완성도의 상한이 아니다. 토큰·구조를 지키되 시각 위계·깊이·여백·제품감 같은 디자인 craft는 적극 발휘하라. 규칙만 지킨 밋밋한 결과는 미완성이다.

---

## 1. 공통 규칙 (유형 무관 — 모든 화면)

### 1.1 토큰 이탈 금지 (값은 design-system.md SSOT, 여기선 "벗어나지 말 것"만)
- **RULE** 색은 semantic 토큰만 사용한다 — `surface/*`, `text/*`, `icon/*`, `status/*/{subtle|default|emphasis}`, `outline/*`, `accent/*`, `background/*`, `primary/*`. 하드코딩 hex·`rgb()`·named color 금지.
- **RULE** Primitive 스케일(`mint-*`, `gray-*`, `red-*`, `amber-*`, `green-*`, `blue-*`, `alpha-*`)을 컴포넌트/화면 코드에 직접 쓰지 않는다. Primitive 는 `tokens.ts`/`globals.css` 내부에서 semantic 이 참조하는 원천으로만 존재한다. **Why:** v4 시절 semantic 커버리지가 부족해 다크모드 작업 시 primitive 를 그대로 꺼내 쓸 수밖에 없었고, 그렇게 만든 화면은 토큰 교체·모드 전환에 무너졌다. v5 는 라이트/다크 양방향을 semantic 만으로 커버하도록 설계했다(실증: Figma `2084-1006` 라이트, `2084-235` 다크 실험).
- **RULE** Tailwind 기본 팔레트(`bg-zinc-900`, `text-slate-500` 등) 금지.
- **RULE** shadcn alias 클래스(`bg-primary`, `text-primary-foreground`, `bg-card`, `bg-muted`, `bg-secondary`, `bg-accent`, `bg-destructive`, `text-foreground`, `text-muted-foreground`, `border-border`, `ring-ring` 등)도 컴포넌트/화면 코드에 쓰지 않는다. v5 canonical semantic 만 사용 — 예: `bg-primary-main`, `text-text-black`, `bg-surface-elevated`, `text-text-primary`, `border-outline-default`, `ring-primary-main`. **Why:** shadcn alias 는 alias 층에서만 존재 의미가 있고 실제 컴포넌트 이름은 Figma canonical 과 일치해야 개발자·디자이너가 같은 어휘로 소통 가능.
- **RULE** `bg-background-*` 은 **페이지 캔버스 배경 전용**이다. 카드/탭/dialog/panel 같은 body 위 표면에는 `bg-surface-{elevated|secondary|tertiary|sunken|disabled}` 를 쓴다. `ring-offset-background-primary` (링 컷아웃) 만 예외.
- **RULE** 필요한 semantic 이 없어 보이면 primitive 를 그대로 꺼내 쓰지 않는다. 먼저 가장 가까운 기존 semantic 으로 대체하고, 그래도 없으면 정본 레포의 `docs/proposals/` 에 신규 semantic 제안을 남긴 뒤 사용처에 `ds-allow` 주석으로 제안 경로를 걸어 진행한다. 승인을 기다리며 멈추지 않되, 근거 없는 primitive 사용은 남기지 않는다.

  > 📌 **제안은 정본 레포에서만 관리한다.** `docs/proposals/` 는 vendoring 대상이 아니므로 이 문서를 가져간 레포에는 그 폴더가 **없다.** 소비 레포에서는 **정본 레포에 PR 로 제안**하고, 로컬 코드의 `ds-allow` 주석에는 그 PR/이슈 링크를 근거로 건다. 로컬에 `docs/proposals/` 를 새로 만들지 않는다 — 제안이 정본에 도달하지 않으면 다음 재동기화에서 그대로 되돌아온다.
  > 정본 레포: https://github.wrtn.club/wrtn-tech/ax-design-system
- **RULE `primary/*` 과 `accent/*` 사용 자리 구분 — 라이트 모드 눈 피로 대응.** 라이트 모드에서 `text-primary-main` (mint-500) 을 텍스트·아이콘 강조에 그대로 쓰면 채도가 높아 눈이 피로해진다. `accent-solid` 토큰(라이트: mint-700 진한 mint · 다크: mint-300 연한 mint · **라이트/다크 자동 양방향 대응**) 을 대신 쓴다.

  | 용도 | 사용 토큰 |
  |---|---|
  | solid 배경 (버튼·활성 nav·hero 원형·pulsing dot 원) | `bg-primary-main` + 내부 `text-text-black` |
  | 상태 인디케이터 점 (통화 중·처리 중·활성) | `bg-primary-main` |
  | 차트·SVG 채우기·라인 | `fill-primary-main` / `stroke-primary-main` |
  | **연한 배경 위 텍스트 강조** (헤로 문구 · 링크 · 활성 라벨) | **`text-accent-solid`** |
  | **연한 배경 위 아이콘 색** (Sparkles·chart 아이콘 · bg-primary-light 위 icon) | **`text-accent-solid`** |
  | **hover 시 강조** (`hover:text-*`) | **`hover:text-accent-solid`** |
  | **outline 배지 안 mint 텍스트** (PK/FK 배지·활성 배지) | **`text-accent-solid`** |

  **한 문장 요약:** 배경 자체가 `primary-main` 이면 내용은 `text-text-black`. 배경이 흰색 · `surface-*` · `primary-light` 이면 위 텍스트·아이콘은 **`text-accent-solid`**. **검증 러닝 (2026-07-30):** 세라젬 hero "데이터로 모읍니다" 강조 텍스트 `text-primary-main` → 디자인 리뷰에서 라이트 눈 피로 지적 → `text-accent-solid` 로 마이그레이션 → 라이트/다크 모두 자연스러워짐. 4개 워크스페이스 PoC 전체 일괄 치환.
- **RULE** 타이포는 템플릿 27 토큰(`text-header-40` ~ `text-plain-12`) 또는 `typography.{key}` helper만. 생짜 `text-sm`/`text-lg`/`text-xl` 금지, 커스텀 타입스케일 재발명 금지.
- **RULE** radius/shadow/spacing도 템플릿 토큰만. 임의값 `rounded-[14px]`·`p-[13px]` 금지.
- **RULE** 필요한 토큰이 없으면 임의값을 화면에 직접 박지 않는다. 가장 가까운 토큰으로 맞추고, 대체가 없으면 정본 레포의 `docs/proposals/` 에 제안을 남긴 뒤 `ds-allow` 주석으로 제안 경로를 걸어 진행한다.
- **RULE** 인라인 `style={{}}`에 값 직접 박기 금지 — `var(--foreground)` 토큰 변수 참조 또는 className.

### 1.2 간격 (템플릿 spacing 토큰)
- **RULE** 간격·패딩·마진은 템플릿 spacing 토큰(`2/4/6/8/12/16/24/32/48/64px`)에서만. 임의 px 금지.
- **PREFER** 컴포넌트 내부 패딩 `p-4`~`p-6`(16~24), 섹션 간 간격 `gap-8`~`gap-16`(32~64).

### 1.3 반응형 (크로스 디바이스)
- **RULE** 모바일 퍼스트로 설계한다. 기본 스타일은 모바일 화면을 기준으로 짜고, 화면이 넓어질수록(`md:`/`lg:`) 데스크탑용 스타일을 덧붙인다.
- **RULE** 좌측에 늘 떠 있던 사이드바·고정 패널은 화면이 좁아지면 햄버거 버튼을 눌렀을 때 옆에서 슬라이드로 나오는 서랍(drawer)/오버레이로 바꾼다. 접히는 기준점은 `lg`(1024px) — 768~1024 구간에서 사이드바를 띄워두면 콘텐츠 영역이 눌려 좁아지므로 1024에서 접는다.
- **RULE** 클릭/터치 타깃은 가로세로 **32×32px** 이상. 마우스 커서와 달리 손가락 끝은 약 1cm 폭이라 더 작은 버튼은 옆 요소를 같이 누르게 된다. 측정 기준: 인터랙티브 요소의 hit area ≥ 32×32px. (WCAG 2.5.5 권장값은 44×44px 이지만, 본 DS 는 앱 UI 의 dense 한 특성을 반영해 32 로 통일 — 데스크탑 dense 어드민·툴바·nav 아이콘 버튼 관행에 맞춤.)
- **PREFER** breakpoint: `sm 640 / md 768 / lg 1024 / xl 1280` (Tailwind 기본 — 관행).
- **PREFER** 화면이 좁아질 때 레이아웃을 재배치(reflow)한다 — 가로로 여러 칸이던 그리드는 위아래로 1단으로 쌓고, 가로 테이블은 카드 리스트로, 가로 메뉴는 햄버거/드로어로 전환.
- ✅ `lg` 미만에서 사이드바를 드로어로 접고, 3열 카드 그리드를 1열로 reflow. 모든 버튼·아이콘 탭 영역 ≥ 32px.
- ❌ 360px 모바일에서 288px 사이드바를 그대로 띄워 콘텐츠 폭이 70px로 짜부 / 32px 아이콘 버튼을 손가락으로 못 누름.

### 1.4 콘텐츠 폭
- **RULE** 본문 한 줄 글자 수는 **≤ 80자** (WCAG 1.4.8 접근성 상한). 긴 본문 블록은 `max-w-prose`류로 폭을 제한해 이 상한을 지킨다.
- **PREFER** 가독성 이상치는 **45~75자**(이상적 ~66자, Butterick). 시각 균형·마케팅 의도 등 디자이너 판단에 따라 늘릴 수 있으나, 위 80자 상한은 유지한다.
- **PREFER** 본문 가독 영역 최대폭은 유형별 스케일로 통일 `[제안]`:
  - 읽기/리스트·설정 중심 → `max-w-5xl` (1024px)
  - 마케팅/랜딩 → `max-w-350` (= 1400px, 시원한 마케팅 폭)
  - 풀폭 작업 캔버스(채팅·에디터) → 폭 제한 없음, 좌우 패딩만
- ✅ 긴 설명 문단은 ~66자에서 줄바꿈되도록 폭 제한, 카드 그리드는 1400까지 넓게.
- ❌ 1400px 풀폭에 본문을 한 줄로 깔아 120자가 넘어가 시선이 줄 끝→다음 줄 시작을 잃음.
- **AVOID** 매 화면 다른 임의 max-width.

### 1.5 z-index / 레이어링
레이어 순서는 정해진 스케일대로. 임의 `z-[9999]` 금지.

| 레이어 | 값 | 용도 |
|---|---|---|
| base | 0 | 일반 콘텐츠 |
| elevated | 10 | floating 요소, hover 카드 |
| sticky-nav | 40 | GNB/헤더, dropdown, popover |
| overlay | 50 | dialog overlay, drawer, sheet |
| tooltip | 60 | tooltip (항상 최상위) |

- **RULE** 오버레이(모달·드로어)는 항상 그 아래 콘텐츠보다 위. tooltip이 최상위.
- **RULE** 임의 z-index 숫자 박기 금지 — 위 5단계 안에서.

### 1.6 인터랙션·접근성
- **RULE** 모든 인터랙티브 요소는 키보드로 도달·조작 가능. Tab 순서 = DOM 순서.
- **RULE** 포커스 시 보이는 포커스 링(`focus-visible:ring-2`). `outline:none`만 두지 말 것.
- **RULE** 모달/다이얼로그: 포커스 트랩 + ESC로 닫힘 + 열릴 때 포커스 진입, 닫힐 때 트리거로 복귀.
- **RULE** 아이콘만 있는 버튼 → `aria-label`. 장식 아이콘 → `aria-hidden`.
- **RULE** 색만으로 정보 전달 금지 (상태는 아이콘+텍스트 병행).
- **RULE** `<div onClick>` 쓸 거면 `role`+`tabIndex`+Enter/Space 핸들러 필수. (가능하면 `<button>`)
- **RULE 원형 아이콘 버튼은 정방향(가로=세로)을 강제한다.** `rounded-full` 만으로는 flex 컨테이너에서 세로로 늘어날 수 있음. **반드시 `size-{n} shrink-0` 로 명시적 정사각형 크기 잠금.** 예: `size='icon' className='size-9 shrink-0 rounded-full'`. **Why:** 세일즈 어시스턴트·다날 composer 송신 버튼이 세로로 늘어져 디자인 리뷰에서 지적 (2026-07-30). 원형 버튼의 정체성이 훼손되지 않으려면 정방향 강제 필요.
- **PREFER** 트랜지션 `transition-* duration-200` 기본(관행). 과한 모션 자제.
- ✅ 모달이 열리면 첫 입력에 포커스 진입, ESC로 닫히고 트리거 버튼으로 포커스 복귀. 아이콘 버튼에 `aria-label="삭제"`.
- ❌ `<div onClick>`로 만든 버튼이 Tab으로 도달 안 됨 / 모달에 ESC·포커스 트랩 없음 / 에러를 빨간 테두리 색으로만 표시.

### 1.7 상태 표현 (모든 데이터 화면)
- **RULE** 비동기 영역은 **로딩 / 비어있음 / 에러 / 정상** 4상태를 모두 처리. 빈 상태를 빈 화면으로 두지 말 것.
- **PREFER** 로딩=스피너 또는 스켈레톤, 에러=메시지+재시도, 빈상태=안내문+다음 액션 유도.

### 1.8 접근성 — 시각 (출처: WCAG)
- **RULE** 색 대비: 본문 텍스트 **≥ 4.5:1**, 큰 텍스트(18px+/14px+굵게)·아이콘·UI 요소 테두리 **≥ 3:1**. (WCAG 1.4.3 / 1.4.11)
- **RULE** 제목 위계: `h1→h2→h3` 순서를 건너뛰지 않는다. 한 페이지에 `h1`은 하나. (스크린리더 탐색)
- **RULE** 이미지·그라데이션 위에 얹는 텍스트도 대비 유지 — 필요 시 어둑한 오버레이.
- ✅ `text-foreground` on `bg-background` 조합으로 4.5:1 확보, KPI 큰 숫자도 3:1 이상.
- ❌ 연한 `foreground-dim`을 본문에 써서 대비 3:1 미만 / `h2` 다음 바로 `h4`.

### 1.9 모션 (출처: Material Motion, WCAG 2.3.3)

일부 사용자는 화면 움직임에 멀미·어지러움을 느껴 OS 의 "동작 줄이기 / 모션 줄이기" 설정을 켜둔다 (Mac · iOS · Windows · Android 공통). UI 는 이 설정을 감지해 트랜지션을 끄거나 약화해야 한다 — CSS 의 `prefers-reduced-motion: reduce` 미디어 쿼리 또는 Tailwind `motion-reduce:` variant 로 처리.

- **RULE** OS "동작 줄이기" 설정 (`prefers-reduced-motion: reduce`) 존중 — 패럴랙스·자동재생·큰 이동은 reduce 시 끄거나 약화. (WCAG 2.3.3)
- **PREFER** duration: 작은 UI 전환 150~200ms / 큰 화면 전환 200~300ms (관행). easing: 진입 `ease-out`, 퇴장 `ease-in`.
- **PREFER** 목적 있는 모션만 — 상태 변화·관계·연속성 표현용. 장식적·무한 반복 모션 자제 (단, 의도된 애니메이션 캔버스·일러스트 영역은 디자이너 판단에 따라 예외).
- ✅ 모달 fade+scale 200ms, OS 가 reduce 설정 켰을 때 즉시 표시.
- ❌ 끝없이 도는 장식 모션 / 500ms+ 굼뜬 전환 / OS reduce 설정 무시.

---

## 2. 구성·배치 원칙 ("왜 여기 두나")

각 규칙은 **RULE → 측정 기준 → ✅/❌** 로 둔다.

### 2.1 시각 위계 — 한 뷰에 1차 액션 하나
- **RULE** 한 화면(또는 구획)에 primary 액션은 1개. 위계는 색·크기·무게·여백으로, 중요도 순서 = 시선 순서.
- ✅ primary 1 + 나머지 secondary/ghost
- ❌ 같은 비중 버튼 3개 나란히

### 2.2 스캔 동선 — F/Z 패턴
- **RULE** 정보 밀집 화면(admin·리스트)은 좌상단부터 훑는 **F패턴** — 핵심 정보·1차 액션을 상단 + 좌측에 배치. 단순/마케팅 화면은 가운데 집중(레이어 케이크·Z동선).
- **측정 기준:** 첫 화면(above the fold)에 핵심 정보·1차 CTA가 들어오는지. 사용자가 스크롤 전 페이지 목적을 파악 가능해야 함.
- ✅ admin 테이블: 제목·검색·주 액션을 상단 바, 중요 컬럼을 왼쪽에. 랜딩: Hero 제목·CTA를 화면 중앙 상단.
- ❌ 주 액션을 우하단·스크롤 한참 아래에 숨김 / 가장 중요한 컬럼이 가로 스크롤 너머에 있음.

### 2.3 근접성 그룹핑 (Gestalt)
- **RULE** 그룹 내부 간격 < 그룹 사이 간격. (예: 라벨–입력 gap-2(8), 필드–필드 gap-6(24) — 숫자는 8pt 그리드 기반 관행)
- ✅ 라벨-입력 붙이고 필드 묶음 사이 띄움
- ❌ 전부 같은 간격 → 묶음 경계 모호

### 2.4 정렬 — 한 기준선
- **RULE** 요소들의 엣지를 공통 기준선(grid·left edge)에 정렬. 정렬 축은 화면당 가능한 적게.
- **측정 기준:** 라벨·입력·버튼의 좌측 엣지가 한 수직선에 맞는지. 들쭉날쭉한 시작점 금지.
- ✅ 폼 라벨과 입력 박스의 좌측 엣지가 동일 수직선에 정렬.
- ❌ 필드마다 들여쓰기가 제각각이라 시선이 좌우로 출렁임.

### 2.5 여백 — 설계 요소
- **RULE** 여백은 채워야 할 빈칸이 아니라 위계·그룹핑 도구. 다만 느슨함만으로는 비전문적이니 밀도와 균형 — 카드/리스트 내부는 밀도 있게, 섹션 사이는 넉넉히.
- **측정 기준:** 섹션 간 간격이 요소 간 간격보다 눈에 띄게 큰지(2.3절 근접성과 일관). 8pt 그리드(관행) 위에서 운용.
- ✅ 섹션 사이 `gap-16`(64), 카드 내부는 `p-4`(16)로 촘촘 — 위계가 여백으로 읽힘.
- ❌ 모든 간격을 동일하게 깔아 어디까지가 한 묶음인지 불명 / 반대로 전부 띄워 화면이 텅 비어 보임.

---

## 3. 공통 컴포넌트 패턴 (유형 가로지름)

> 📌 **3.1~3.3의 접근성·키보드 규칙은 WAI-ARIA APG가 출처다. 우리가 쓰는 Radix(shadcn 기반)가 APG를 구현한 "원조"이므로, Radix 동작이 곧 APG 준수다.**

### 3.1 액션·버튼 위계
- **RULE** 한 화면(또는 영역)에 primary 버튼은 하나. 나머지는 secondary/ghost.
- **PREFER** 위계: primary(채움) > secondary(아웃라인) > tertiary/ghost(텍스트).
- **RULE** destructive(삭제 등)는 destructive 토큰으로 시각 구분 + 확인 단계(3.3절 dialog).
- **PREFER** 확인/취소 버튼 순서: 주 액션을 오른쪽, 취소는 왼쪽 또는 ghost — 프로젝트 내 일관되게(관행).
- **RULE** 비활성: `disabled` + 시각(opacity) + `cursor-not-allowed`.
- ✅ 모달 푸터에 primary "저장" + ghost "취소" 한 쌍, 삭제는 destructive 색 + 확인 dialog.
- ❌ 같은 채움 버튼 3개 나란히 / 삭제 버튼이 일반 버튼과 동일 색 + 확인 없이 즉시 실행.

### 3.2 폼·입력
- **RULE** 모든 입력에 연결된 라벨(`<label htmlFor>` + `id`). placeholder를 라벨 대용으로 쓰지 말 것.
- **PREFER** 라벨은 입력 위(top-aligned) — 스캔·모바일에 유리(관행).
- **PREFER** 검증 타이밍: 제출 시 + 필드 blur 후. 타이핑 중 실시간 빨간불은 피함(관행).
- **RULE** 에러는 색만이 아니라 텍스트로 + 해당 필드 근처 + `aria-invalid`/`aria-describedby`.
- **PREFER** 필수 표기 일관(`*` 또는 "필수"), 선택 항목엔 "(선택)".
- **PREFER** 관련 필드는 그룹핑(2.3절 근접성), 긴 폼은 섹션 분할. 제출 버튼은 primary 하나.
- ✅ 라벨이 입력 위에 붙고, 에러는 필드 바로 아래 텍스트 + `aria-describedby`로 연결.
- ❌ placeholder "이름 입력"이 라벨 대용 → 입력 후 무슨 필드인지 사라짐 / 에러를 빨간 테두리로만 표시.

### 3.3 피드백: toast / dialog / inline (언제 무엇을)


| 방식 | 언제 | 특징 |
|---|---|---|
| **inline** (필드·영역 내) | 폼 검증, 맥락 있는 경고, 영역 단위 에러 | 비차단, 위치 고정 |
| **toast** | 비차단 성공/완료 알림 | 일시적·자동 소멸, 짧게 |
| **dialog/modal** | 확인 요구, destructive 확인, 진행 차단 에러 | 차단, 사용자 응답 필요 |

- **RULE** 파괴적·되돌릴 수 없는 액션은 dialog로 확인. 단순 성공 알림은 toast (모달 X).
- **RULE** toast는 한 줄 텍스트로 짧게. 에러 상세·해결 안내는 inline 또는 dialog.
- ✅ "저장 완료"는 자동 소멸 toast, "정말 삭제하시겠습니까?"는 확인 dialog, 폼 검증 실패는 필드 옆 inline.
- ❌ 단순 성공을 모달로 차단 / 삭제를 확인 없이 즉시 실행 / 긴 에러 해결 안내를 5초 후 사라지는 toast에 욱여넣음.

### 3.4 데이터 테이블 [주로 admin] (NN/g — Designing Tables)
- **PREFER** 행 15개↑면 헤더 sticky. 정렬·검색 제공.
- **PREFER** 숫자는 우측 정렬, 텍스트는 좌측. 행 밀도는 compact 기본.
- **PREFER** 행 액션은 행 끝 또는 hover 시 노출. 데이터 많으면 페이지네이션/가상 스크롤.
- **RULE** 빈 테이블 = 1.7절 빈상태. 로딩 = 스켈레톤 행.

### 3.5 필터 [주로 admin]
- **PREFER** 필터 위치: 상단 sticky 바 또는 좌측 패널.
- **RULE** 활성 필터는 제거 가능한 chip으로 노출. 2개↑ 활성 시 "전체 해제" 제공.
- **PREFER** 적용 방식(즉시 반영 vs "적용" 버튼)은 프로젝트 내 일관되게. 결과 0건이면 빈상태 + 필터 완화 안내.

---

## 4. 화면 유형별 레시피 (먼저 "내가 뭘 만드는지" 고르고 → 해당 골격)

> 4유형은 기존 PoC에서 실제 관찰된 것. 새 화면은 이 중 하나로 분류부터. 각 archetype의 **anatomy(구역 + 권장 간격 + 예시 구조)**는 위계·일관성 원칙에 근거하되, 구체 px·섹션 순서는 관행이다.

### 4.1 랜딩 / 마케팅

> ⏸ **재검토 예정 (2026-07-23 디자인 리뷰)** — 이전 골격/anatomy 규칙은 랜딩 콘텐츠가 무엇을 전할지 모르는 상태에서 와이어프레임을 미리 못박아 평면적이고 메시지 전달력이 부족한 결과가 나옴. 랜딩 archetype 은 컨텐츠·톤·목적에 따라 자유롭게 구성되어야 하므로 별도 재검토 후 갱신.

### 4.2 콘솔 / Admin
**골격 (PREFER):** `[고정 사이드바 내비] + [상단 탑바(타이틀+우상단 주 액션)] + [콘텐츠(카드/테이블 그리드)]`

**Anatomy (px는 관행):**
- 구역: `좌측 내비 사이드바` / `상단 탑바(제목 + 우상단 주 액션)` / `메인 콘텐츠(카드·테이블)`.
- 권장 간격: 사이드바 폭 288px(관행), 콘텐츠 패딩 `p-6`(24), 카드 간 `gap-6`(24).
- 예시 구조: `<aside w-72>` + `<main>(<header>+<section grid>)`.

- **PREFER** 내비 사이드바 폭 **288px** `[제안: w-72]`(관행), `lg` 미만 드로어(1.3절).
- **PREFER** 페이지 헤더: 제목 + 주 액션 우상단, 필요 시 breadcrumb/컨텍스트 하단. (Material app bar 관례 — 관행)
- **RULE** 현재 위치(활성 메뉴) 항상 시각 표시.
- ✅ 활성 메뉴 하이라이트 + 제목·"새로 만들기"를 탑바 좌/우로 분리, 본문은 F동선(2.2절) 상단부터.
- ❌ 활성 메뉴 표시 없음 / 주 액션이 콘텐츠 맨 아래 묻힘.

### 4.3 워크스페이스 / 단일 툴
**골격 (PREFER):** `[설정/입력 사이드 패널] + [메인 작업 캔버스 1개]`

**Anatomy (px는 관행):**
- 구역: `좌측 설정/입력 패널` / `메인 작업 캔버스(핵심 작업 1개)`.
- 권장 간격: 작업 패널 폭 400px(관행), 캔버스 풀폭 + 좌우 패딩.
- 예시 구조: `<aside w-100>`(= 400px) + `<main canvas>`.

- **PREFER** 작업 패널 폭 **400px** (콘솔 내비보다 넓음 — 관행). `lg` 미만 오버레이(1.3절).
- **PREFER** 메인 캔버스는 풀폭, 핵심 작업 하나에 집중(2.1절). 부가 기능은 패널 안 접이식 섹션.
- **RULE** 작업 진행 상태(업로드/분석/완료)를 캔버스에 명확히 피드백.
- ✅ 좌측 400px 설정 패널 + 우측 결과 캔버스, 진행률을 캔버스에 명시.
- ❌ 설정·결과·로그를 한 화면에 동급으로 쪼개 어디가 메인인지 불명.

### 4.4 콘텐츠 뷰어 / 리스트
**골격 (PREFER):** `header(타이틀+설명) → [가운데 정렬 단일 컬럼] → 카드 그리드/리스트 → (선택)상세`

**Anatomy (px는 관행):**
- 구역: `상단 header(제목 + 설명)` / `가운데 단일 컬럼` / `카드 그리드/리스트` / `(선택) 상세`.
- 권장 간격: 콘텐츠 `max-w-5xl mx-auto`(1024), 좌우 `px-6`, 카드 `gap-6`(24).
- 예시 구조: `<header>` → `<main max-w-5xl>(<ul/grid>)` → `<detail>`.

- **PREFER** 콘텐츠 `max-w-5xl mx-auto`, 좌우 패딩 `px-6`.
- **RULE** 목록이 비면 1.7절 빈상태. 다단계 탐색이면 현재 단계(Step/breadcrumb) 표시.
- **PREFER** 목록→상세 전환 시 "뒤로" 경로 항상 제공.
- ✅ 중앙 정렬 단일 컬럼 + 일관된 카드 간격, 빈 목록에 안내문 + 다음 액션.
- ❌ 카드 폭·간격이 행마다 달라 정렬 무너짐 / 빈 목록을 백지로 둠.

---

## 5. drift 해소 — 표준값 결정표 (검토요망)

기존 PoC가 제각각이던 값을 하나로. **`[제안]`은 잠정 표준 — 승인을 기다리지 말고 그대로 쓰고, 반례가 나오면 사유와 함께 PR 로 갱신한다.**

| 항목 | 기존 (제각각) | 제안 표준 |
|---|---|---|
| 사이드바 접는 breakpoint | md(768) / lg(1024) | **lg (1024)** |
| 콘솔 내비 사이드바 폭 | 288 | **288 (w-72)** |
| 워크스페이스 작업 패널 폭 | 400 | **400** |
| 랜딩 콘텐츠 최대폭 | 1400 / 1200 | **1400** |
| 뷰어/리스트 최대폭 | 1024 | **1024 (max-w-5xl)** |
| 터치 타깃 최소 | (미정) | **32×32** |

> 토큰 차원의 drift(타이포 재발명, radius 14 vs 12 등)는 별도 표준이 아니라 "템플릿 토큰으로 복귀"가 곧 해소다 (1.1절).

---

## 6. Counter-examples (이러면 거부/교체)

- ❌ `text-xl`, 커스텀 `text-hero` → 템플릿 `text-header-*`/`text-plain-*`.
- ❌ `rounded-[14px]`, `p-[13px]`, `z-[9999]` → 템플릿 토큰 / 1.5절 레이어 스케일.
- ❌ 하드코딩 `#079883` / `bg-zinc-900` → `bg-primary` 등 시맨틱 토큰.
- ❌ `<div onClick>` 인데 키보드 핸들러 없음 → `<button>` 또는 role+key.
- ❌ placeholder를 라벨 대용으로 사용 → 연결된 `<label>`.
- ❌ 한 화면에 primary 버튼 여러 개 → 하나만.
- ❌ 단순 성공을 모달로 차단 → toast. / 삭제를 확인 없이 즉시 실행 → dialog 확인.
- ❌ 모달에 ESC·포커스트랩 없음 → 디자인 시스템 Dialog.
- ❌ 로딩만 처리하고 빈상태/에러 없음 → 4상태 모두.

---

## 7. 빠른 디스패치 ("이 작업엔 어디 보나")

| 만들 것 | 본다 |
|---|---|
| 새 화면 시작 | 4번 섹션에서 유형 분류 → 레시피 + 1·2번 섹션 |
| 버튼·CTA 배치 | 3.1절 + 2번 섹션 |
| 폼·입력 | 3.2절 |
| 알림·확인·에러 | 3.3절 + 1.7절 |
| 테이블·필터 (admin) | 3.4·3.5절 |
| 사이드바 폭/접힘 | 4.2·4.3절 + 5번 섹션 |
| 레이어/모달 쌓임 | 1.5절 |
| 간격·타이포·색 토큰 | 1.1·1.2절 → 값은 `design-system.md` |

---

## 8. 이 문서가 다루지 않는 것 (Known Gaps)

Claude는 아래를 **이 문서에서 찾지 말고** 표시된 출처를 따른다. 출처가 "미정"인 항목은 멈추지 말고 가장 가까운 기존 패턴을 참고해 진행하되, **무엇을 어떤 근거로 정했는지 PR 에 남긴다.** 없는 패턴을 지어내 놓고 규칙인 것처럼 쓰지 말 것.

- **토큰 값**(색·타이포·spacing 수치) → `docs/design-system.md` (SSOT)
- **shadcn variant·utility 클래스 어휘** → `docs/component-variants.md`
- **서비스별 도메인 로직·플로우** → 각 PoC의 SPEC/PRD
- **복합 위젯**(차트·지도·캘린더·리치 에디터 등)의 내부 디자인 → 미정. 기존 PoC 구현(차트는 [chart-color-tokens.md](https://github.wrtn.club/wrtn-tech/ax-design-system/blob/develop/docs/proposals/chart-color-tokens.md))을 참고해 진행하고, 새로 정한 규칙은 정본 레포의 `docs/proposals/` 에 남긴다 (1.1절 📌 참조). 이 폴더는 vendoring 대상이 아니라 소비 레포에는 없으므로 웹 링크로 연다.
- **모션 디테일**(duration/easing 체계) → 1.6절의 기본값 외 미정 (추후 후보)

---

## 9. 적용 우선순위 요약

1. 토큰은 템플릿 거 그대로 (1.1) → 2. 유형 분류(4) → 3. 골격 + 공통규칙(1) + 구성원칙(2) → 4. 컴포넌트 패턴(3) → 5. 4상태·접근성 확인(1.6·1.7) → 6. 못 정하면 8번 섹션대로 문의.

---

## 10. 프로젝트별 슬롯 (받은 사람이 작성)

위 0~9번 섹션(제네릭)은 수정하지 말고, 프로젝트 고유 사항만 여기에.

### 이 레포 정보 (service-planning-agent — 서비스 기획 워크플로우)

- **성격:** 앱 레포가 아니라 **기획 산출물 생성 워크플로우 레포**다. 앱 소스(`src/`·React·TS)가 없고, 디자인 표면은 스킬 11 이 생성하는 **화면 HTML**(`docs/[프로젝트명]/ui/screens/*.html`)이다.
- **라이트/다크:** 라이트 단일. 화면 37개 중 `dark:`·`prefers-color-scheme` 사용 0건 — 산출물이 고객 리뷰·PDF 출력을 전제로 하기 때문.
- **주 사용 유형:** 워크스페이스(`layout-types/01-workspace.md`). 유형 판별은 `00-type-selection.md` 기준으로 프로젝트마다 다시 한다.
- **보유 문서:** `required` 6종 전부 + `scoped` 중 `01-workspace.md`. `02-admin.md`(scoped)는 어드민 유형 화면에 착수할 때 받는다. `proposals/**`·`releases/**`(excluded)는 받지 않는다.

### 의도적 편차 (템플릿 대비)

| 항목 | 정본 | 이 레포 | 사유 |
|---|---|---|---|
| 거버넌스 문서 위치 | `docs/` | `.claude/design-system/` | 이 레포의 `docs/` 는 고객 산출물 유출 방지를 위해 통째로 git 추적 제외(.gitignore). `docs/` 에 두면 문서가 추적되지 않는다. |
| 게이트 스크립트 위치 | `scripts/` | `.claude/scripts/` | 이 레포의 스크립트 규약(`validate_traceability.py` 등이 모두 여기). |
| 토큰 전달 방식 | `globals.css` `@theme` + `tokens.ts` | 없음 (Tailwind CDN) | 화면 HTML 이 `cdn.tailwindcss.com` 을 직접 물고 빌드 단계가 없다. semantic 토큰 레이어가 존재하지 않아 현재 화면은 raw Tailwind 유틸리티를 쓴다. |
| `check-design-tokens.mjs` 스캔 루트 | 스크립트 기준 `..` 고정 | `--root=<dir>` 로 받음 | 산출물이 이 레포가 아니라 **프로젝트별 독립 저장소**에 있다. 고정하면 스캔 0건 → 공허한 "이탈 없음". |
| `check-ds-sync.mjs` 사본 경로 | `docs/**` | `design-system/**` → `docs/**` 정규화 | 위 문서 위치 편차의 귀결. 패치 없으면 전건이 "manifest 범위 밖" 으로 빠져 **한 건도 대조 않고 통과**한다. |
| 게이트 강제력 | 차단(ERROR 시 exit 1) | **조언 모드 기본 + 옵트인 차단** | 도입 시점 baseline 이 ERROR 수천 건이라 차단으로 켜면 기존 프로젝트 커밋이 전부 막힌다(brownfield 무결성 RULE). `.design-gate-strict` 또는 `DESIGN_GATE=strict` 로 저장소별 옵트인. |

> 로컬 패치의 **내용·근거**는 각 스크립트 상단 `[로컬 패치]` 주석이 정본이다. 재동기화 시 그 주석대로 재적용한다.

### baseline (2026-08-27 재측정, 정본 `9a6e7c5` 게이트)

커밋 게이트 ④의 적용 범위인 **`ui/screens`** 기준 — 전체 **ERROR 3,865건 · WARN 874건 · ds-allow 면제 0건**.

| 프로젝트 | 화면 | ERROR | WARN |
|---|---|---|---|
| `interview-digest` | 7 | 381 | 457 |
| `kyobo_lifeplanet_ai_salesbot` | 14 | 1,349 | 268 |
| `wrtnax-aicc-platform` | 16 | 2,135 | 149 |
| `wremember` | 0 (Phase 3 미착수) | 0 | 0 |

- **범위 밖 백로그:** `assets/wireframes/**`(76개, 저해상도 와이어프레임)를 포함한 전체 스캔은 ERROR 6,957건. 와이어프레임은 **의도적 그레이스케일**이라 토큰 대조 대상이 아니므로 마이그레이션 대상으로 잡지 않는다.
- `ui/screens/index.html` 은 `generate_screen_index.py` 자동 생성물이라 vendored(WARN)로 강등한다. 위반은 생성기에서 고친다.
- 기존 3개 프로젝트는 DS 도입 이전 산출물이라 ERROR 0 이 아니다. **신규 프로젝트부터** strict 옵트인으로 ERROR 0 을 유지한다.
- 재측정 명령: `node .claude/scripts/check-design-tokens.mjs --root=docs/[프로젝트명] --scope=ui/screens`

### 재동기화 이력

| 시점 | 정본 커밋 | 결과 |
|---|---|---|
| 2026-08-03 | `f430de0` | 최초 vendoring (문서 4종) |
| 2026-08-27 | `9a6e7c5` | 문서 7종으로 확대(`vendor:` 등급 계약 도입). **토큰 값 변경 0건** — 기존 화면 재작업 불필요. 게이트에 `check-ds-sync.mjs` 추가, `offscale-spacing` 규칙(WARN) 신설 |

### 미적용 항목 (이 레포에 해당 없음)

`tokens.ts`·`typography.ts`·shadcn 컴포넌트 포팅·`package.json`·빌드/lint/런타임 게이트 — 앱 소스가 없어 적용 대상이 아니다. 이 레포에 앱 코드가 생기면 그때 정본 절차대로 도입한다.

`check-adoption-contract.mjs`(정본 자체 점검용)·`/sync-figma`·`/apply-tokens` 는 정본 전용이라 받지 않는다.

---

## 출처 (References)

이 playbook의 디자인 규칙이 근거한 표준·연구·책 목록 (참고·전파용). 본문엔 태그를 달지 않으며, "왜 이 규칙?"이 궁금할 때 여기서 확인한다.

| 이름 | 링크 | 유형 |
|---|---|---|
| NN/g — F-Shaped Pattern for Reading | https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/ | 연구 |
| NN/g — Text Scanning Patterns: Eyetracking | https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/ | 연구 |
| Laws of UX (Jon Yablonski) | https://lawsofux.com/ | 원칙 모음 |
| Laws of UX — Law of Proximity (Gestalt) | https://lawsofux.com/law-of-proximity/ | 원칙 |
| Butterick's Practical Typography — Line length | https://practicaltypography.com/line-length.html | 표준 |
| WCAG 2.1/2.2 Understanding (W3C) — 인용: 1.4.3 대비(4.5:1/3:1), 1.4.8 줄길이(≤80자), 2.3.3 모션, 2.5.5 터치타깃(44px) | https://www.w3.org/WAI/WCAG21/Understanding/ | 표준 |
| WAI-ARIA Authoring Practices Guide (W3C) — Radix가 구현하는 원본 | https://www.w3.org/WAI/ARIA/apg/ | 표준 |
| Material Design 3 — Layout | https://m3.material.io/foundations/layout | 플랫폼 가이드 |
| Material Design 3 — Motion | https://m3.material.io/styles/motion/overview | 플랫폼 가이드 |
| Apple Human Interface Guidelines | https://developer.apple.com/design/human-interface-guidelines | 플랫폼 가이드 |
| Refactoring UI (Wathan & Schoger) | https://www.refactoringui.com/ | 책 |
| NN/g — 10 Usability Heuristics | https://www.nngroup.com/articles/ten-usability-heuristics/ | 표준 |
