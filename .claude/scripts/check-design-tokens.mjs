#!/usr/bin/env node
// 디자인 토큰 이탈 정적 검사 — "절대값(하드코딩) 금지, 토큰만 사용" 강제.
//
// CLAUDE.md / docs/design-playbook.md 1.1 의 토큰 이탈 금지 RULE 을 코드로 점검한다.
// ax-design-system 를 vendoring 한 레포가 공통으로 들고 가는 게이트
// (정본 위치: ax-design-system/scripts/check-design-tokens.mjs).
//
// 왜 필요한가 (AXT-725):
//   - 기존 ESLint 는 inline `style={{ color: '#..' }}` 만 잡고 Tailwind 임의값·
//     primitive 팔레트·raw 타이포는 못 잡았다.
//   - /design-review 게이트는 "변경한 파일"만 봐서 vendored shadcn `ui/` 와
//     WebGL shader 의 잔여 drift 를 통과시켰다.
//   이 스크립트는 그 사각지대(모든 src 파일)를 정적으로 닫는다.
//
// 심각도:
//   - ERROR  : authored 레이어(직접 작성하는 코드)의 이탈 → CI 차단.
//   - WARN   : (a) vendored 레이어(shadcn `ui/`, 최상위 시각 컴포넌트)의 이탈,
//     (b) v5 마이그레이션 규칙 — shadcn alias 클래스 / mint·gray·alpha primitive 직접 사용
//     (playbook 1.1 RULE, 잔여 사용 정리 후 ERROR 승격 예정) → 추적/백로그.
//     (--strict 시 WARN 도 exit 1 — 백로그 정리를 강제할 때 사용)
//
// 명시적 예외: 위반이 불가피한 줄에 `ds-allow` 주석을 달면 그 줄은 면제된다
//   (예: WebGL shader 는 vec3 리터럴 색이 강제되므로
//    `// ds-allow: shader 는 리터럴 색 필요 — --mint 토큰 미러`).
//   침묵하는 예외 대신 "감사 가능한 예외"를 남긴다.
//
// 사용:
//   node scripts/check-design-tokens.mjs            -- 요약을 stdout 으로 출력 (ERROR 있으면 exit 1)
//   node scripts/check-design-tokens.mjs --report   -- test-results/design-token-audit.md 생성
//   node scripts/check-design-tokens.mjs --strict   -- WARN 이 1건이라도 있으면 exit 1
//   node scripts/check-design-tokens.mjs --scope=src/components,src/lib
//                                                   -- 적용 범위를 한정한다. 범위 안 ERROR 만 차단하고,
//                                                      범위 밖 ERROR 는 "백로그" 로 따로 세어 출력한다.
//                                                      (brownfield 점진 마이그레이션용 — 침묵 제외 금지)
//
// 단순 정적 휴리스틱이므로 false positive 가 있을 수 있다. /design-review 와 함께 사용한다.

// ─────────────────────────────────────────────────────────────────────────
// [로컬 패치 — service-planning-agent 워크플로우 레포]
//   정본(ax-design-system @ f430de0)은 `<레포>/src/**/*.{ts,tsx,css}` 를 고정
//   스캔한다. 이 레포에는 앱 소스가 없고 디자인 표면이 기획 산출물인 화면
//   HTML(`ui/screens/*.html`, Tailwind 클래스 사용)이라, 정본 그대로 두면
//   스캔 대상 0건 → 공허한 "이탈 없음" 이 되어 게이트로서 거짓말을 한다.
//   그래서 아래 3가지만 로컬 패치했다 (탐지 규칙·심각도·RULE 수치는 무수정):
//     ① `--root=<dir>` 로 스캔 루트를 받는다 (기본: 이 스크립트 기준 레포 루트)
//     ② 스캔 확장자에 `.html` 추가
//     ③ 자동 생성물 `ui/screens/index.html` 은 vendored(WARN) 로 강등
//   ⚠️ 정본 재동기화 시 이 패치를 재적용해야 한다.
// ─────────────────────────────────────────────────────────────────────────

import { readdir, readFile, mkdir, writeFile } from 'node:fs/promises';
import { join, relative, dirname, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));

const argv = process.argv.slice(2);
const args = new Set(argv);
const REPORT = args.has('--report');
const STRICT = args.has('--strict');

// [로컬 패치 ①] 스캔 루트 — `.claude/scripts/` 에 두므로 기본값은 두 단계 위(레포 루트)
const ROOT_ARG = argv.find((a) => a.startsWith('--root='))?.slice(7);
const projectRoot = ROOT_ARG
  ? resolve(process.cwd(), ROOT_ARG)
  : join(here, '..', '..');
const scanRoot = projectRoot;

// [로컬 패치 ②] 스캔 확장자 + 순회 제외 디렉토리
const SCAN_EXT = ['.ts', '.tsx', '.css', '.html'];
const IGNORE_DIRS = new Set([
  'node_modules',
  '.git',
  '.next',
  'dist',
  'build',
  '_archive',
  'test-results',
  '__pycache__',
  '.venv',
  'venv',
]);

// ── 적용 범위 (--scope=a,b) ───────────────────────────────────────────────
//   brownfield 는 한 번에 전 화면을 옮기지 못한다. 범위를 한정해 "그 안에서는
//   ERROR 0" 을 만들되, 범위 밖 잔여 이탈은 숨기지 않고 백로그로 세어 보고한다.
const SCOPE = (argv.find((a) => a.startsWith('--scope='))?.slice(8) ?? '')
  .split(',')
  .map((s) => s.trim().replace(/^\.\//, '').replace(/\/$/, ''))
  .filter(Boolean);
const inScope = (rel) =>
  SCOPE.length === 0 || SCOPE.some((p) => rel === p || rel.startsWith(p + '/'));

// ── 토큰 정의 파일: 여기서는 하드코딩 값이 정상(SSOT 그 자체) ─────────────
//   경로 무관으로 판별해 nextjs(`src/app/globals.css`)·vite(`src/globals.css`)·
//   vendoring 한 레포 어디서나 동일하게 동작하게 한다.
function isTokenDef(rel) {
  const base = rel.split('/').pop();
  if (base === 'globals.css') return true; // CSS 변수 정의 (값의 출처)
  if (/(^|\/)theme\/tokens\.ts$/.test(rel)) return true; // TS 미러
  return false;
}

// ── vendored 레이어: 외부에서 가져온 코드. 이탈은 WARN(추적) 으로 강등 ──────
//   - shadcn 프리미티브: src/components/ui/**
//   - 최상위 시각 컴포넌트(react-bits 류): src/components/*.tsx (common/ 제외)
function isVendored(rel) {
  if (rel.startsWith('src/components/ui/')) return true;
  // src/components/Xxx.tsx (한 단계 깊이, common/ui 하위가 아닌 느슨한 컴포넌트)
  if (/^src\/components\/[^/]+\.tsx$/.test(rel)) return true;
  // [로컬 패치 ③] generate_screen_index.py 자동 생성물 — 위반은 생성기에서 고친다
  if (/(^|\/)ui\/screens\/index\.html$/.test(rel)) return true;
  return false;
}

// ── 탐지기 ────────────────────────────────────────────────────────────────
// 1) 하드코딩 색 리터럴 (hex / rgb / hsl) — 모든 컨텍스트(임의값 안 포함)
const COLOR_LITERAL_RE = /#[0-9a-fA-F]{3,8}\b|(?:rgb|rgba|hsl|hsla)\s*\(/g;

// 2) 금지된 Tailwind primitive 팔레트
//    (mint/gray/alpha 는 DS primitive — 아래 primitive-direct 규칙이 WARN 으로 별도 추적)
const PRIMITIVE_RE =
  /\b(?:bg|text|border|ring|ring-offset|from|to|via|fill|stroke|decoration|outline|divide|placeholder|caret|accent|shadow)-(?:zinc|slate|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b/g;

// 3) raw Tailwind 타이포 사이즈 (27 토큰 밖 — text-header-* / text-plain-* 와 충돌 안 함)
const RAW_TYPO_RE = /\btext-(?:xs|sm|base|lg|xl|[2-9]xl)\b/g;

// 4) 임의값 utility-[...] — 값 유틸리티에 한정(변형 셀렉터 [&_svg], data-[..] 는 제외)
const VALUE_UTILS =
  '(?:text|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|gap-x|gap-y|w|h|size|min-w|max-w|min-h|max-h|top|bottom|left|right|inset|inset-x|inset-y|rounded|leading|tracking|basis|indent|translate-x|translate-y|space-x|space-y)';
const ARBITRARY_RE = new RegExp(
  `(?<![\\w-])${VALUE_UTILS}-\\[([^\\]]+)\\]`,
  'g',
);
// 임의값 안에서 "토큰 없이 못 표현하는" 것은 허용: 뷰포트/백분율/계산/변수참조 등
const ARBITRARY_ALLOW_RE =
  /vh|vw|dvh|svh|lvh|%|calc|min\(|max\(|clamp\(|var\(|color-mix|fr|ch|ex/;
const ARBITRARY_KEYWORD_ALLOW = new Set([
  'inherit',
  'auto',
  'initial',
  'unset',
  'none',
  'currentColor',
  'transparent',
]);
const FIXED_LEN_RE = /^-?\d*\.?\d+(px|rem|em)$/;

// 5) shadcn alias 클래스 — v5 canonical semantic 만 허용 (playbook 1.1 RULE).
//    잔여 사용 정리(마이그레이션) 전까지 WARN. 예외: ring-offset-background-primary.
const COLOR_PREFIX =
  '(?:bg|text|border|ring|fill|stroke|divide|outline|decoration|placeholder|caret|from|to|via|shadow)';
const SHADCN_ALIAS_RE = new RegExp(
  '(?<![\\w-])(?:' +
    [
      `${COLOR_PREFIX}-background(?:-2|-elevated)?`,
      `${COLOR_PREFIX}-foreground(?:-muted|-dim|-disabled|-invert)?`,
      `${COLOR_PREFIX}-card(?:-foreground)?`,
      `${COLOR_PREFIX}-popover(?:-foreground)?`,
      `${COLOR_PREFIX}-muted(?:-foreground)?`,
      `${COLOR_PREFIX}-secondary(?:-foreground)?`,
      `${COLOR_PREFIX}-primary(?:-foreground)?`,
      `${COLOR_PREFIX}-accent(?:-foreground|-soft)?`,
      `${COLOR_PREFIX}-(?:destructive|success|warning|info|error)(?:-foreground|-soft|-emphasis|-base|-default)?`,
      '(?:border|divide)-border(?:-subtle|-strong)?',
      'border-input',
      'ring-ring',
      'ring-offset-background',
    ].join('|') +
    ')(?![\\w-])',
  'g',
);

// 6) DS primitive 직접 사용 (mint/gray/alpha) — semantic 만 허용 (playbook 1.1 RULE — v5).
//    (red/amber/green/blue 는 @theme 미노출이라 primitive-palette 가 ERROR 로 잡는다.)
const PRIMITIVE_DIRECT_RE = new RegExp(
  `(?<![\\w-])${COLOR_PREFIX}-(?:(?:mint|gray)-\\d{2,4}|alpha-(?:black|white|mint)-\\d{2})(?![\\w-])`,
  'g',
);

const RULES = {
  'hardcoded-color': '하드코딩 색 리터럴 (hex/rgb/hsl) — 시맨틱 토큰 사용',
  'primitive-palette':
    '금지된 Tailwind primitive 팔레트 — mint-*/gray-*/시맨틱 토큰만',
  'raw-typography':
    'raw Tailwind 타이포 사이즈 — text-{header|title|body|label|plain}-* 27 토큰 사용',
  'arbitrary-size': '임의 고정 치수값 — spacing/radius/typography 토큰 사용',
  'arbitrary-other': '임의값 — 토큰으로 표현 가능한지 확인',
  'shadcn-alias':
    'shadcn alias 클래스 — v5 canonical semantic 사용 (playbook 1.1, 마이그레이션 백로그)',
  'primitive-direct':
    'DS primitive 직접 사용 — semantic 토큰 사용 (playbook 1.1, 마이그레이션 백로그)',
};

const findings = [];
let allowlisted = 0;

function scanLine(rel, vendored, lineNo, line, prevLine) {
  // ds-allow 주석이 같은 줄 또는 바로 윗줄에 있으면 면제(감사 가능한 명시적 예외)
  if (/ds-allow/.test(line) || /ds-allow/.test(prevLine)) {
    // 실제로 잡혔을 법한 패턴이 있을 때만 카운트(주석만 있는 줄 제외)
    if (
      COLOR_LITERAL_RE.test(line) ||
      PRIMITIVE_RE.test(line) ||
      RAW_TYPO_RE.test(line) ||
      SHADCN_ALIAS_RE.test(line) ||
      PRIMITIVE_DIRECT_RE.test(line) ||
      /\[/.test(line)
    ) {
      allowlisted++;
    }
    COLOR_LITERAL_RE.lastIndex = 0;
    PRIMITIVE_RE.lastIndex = 0;
    RAW_TYPO_RE.lastIndex = 0;
    SHADCN_ALIAS_RE.lastIndex = 0;
    PRIMITIVE_DIRECT_RE.lastIndex = 0;
    return;
  }

  const sev = vendored ? 'WARN' : 'ERROR';
  const add = (rule, severity, col) =>
    findings.push({
      rel,
      lineNo,
      col,
      rule,
      severity,
      snippet: line.trim().slice(0, 160),
    });

  let m;
  COLOR_LITERAL_RE.lastIndex = 0;
  while ((m = COLOR_LITERAL_RE.exec(line)))
    add('hardcoded-color', sev, m.index + 1);

  PRIMITIVE_RE.lastIndex = 0;
  while ((m = PRIMITIVE_RE.exec(line)))
    add('primitive-palette', 'ERROR', m.index + 1); // 어디서든 ERROR

  RAW_TYPO_RE.lastIndex = 0;
  while ((m = RAW_TYPO_RE.exec(line))) add('raw-typography', sev, m.index + 1);

  // v5 마이그레이션 규칙 — 레이어 무관 WARN (잔여 사용 정리 후 ERROR 승격)
  SHADCN_ALIAS_RE.lastIndex = 0;
  while ((m = SHADCN_ALIAS_RE.exec(line)))
    add('shadcn-alias', 'WARN', m.index + 1);

  PRIMITIVE_DIRECT_RE.lastIndex = 0;
  while ((m = PRIMITIVE_DIRECT_RE.exec(line)))
    add('primitive-direct', 'WARN', m.index + 1);

  ARBITRARY_RE.lastIndex = 0;
  while ((m = ARBITRARY_RE.exec(line))) {
    const content = m[1].trim();
    if (/#[0-9a-fA-F]{3,8}|(?:rgb|hsl)a?\(/.test(content)) continue; // 색은 hardcoded-color 가 이미 잡음
    if (ARBITRARY_ALLOW_RE.test(content)) continue; // 뷰포트/계산/변수참조 허용
    if (ARBITRARY_KEYWORD_ALLOW.has(content)) continue;
    if (FIXED_LEN_RE.test(content)) add('arbitrary-size', sev, m.index + 1);
    else add('arbitrary-other', sev, m.index + 1);
  }
}

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) {
      if (IGNORE_DIRS.has(e.name) || e.name.startsWith('.')) continue;
      await walk(full);
      continue;
    }
    const ext = extname(e.name);
    if (!SCAN_EXT.includes(ext)) continue;
    if (/\.(test|spec)\.(ts|tsx)$/.test(e.name)) continue;
    const rel = relative(projectRoot, full).split('\\').join('/');
    if (isTokenDef(rel)) continue;
    const vendored = isVendored(rel);
    const content = await readFile(full, 'utf8');
    const fileLines = content.split('\n');
    fileLines.forEach((line, i) =>
      scanLine(rel, vendored, i + 1, line, i > 0 ? fileLines[i - 1] : ''),
    );
  }
}

await walk(scanRoot);

// ── 집계 ──────────────────────────────────────────────────────────────────
const allErrors = findings.filter((f) => f.severity === 'ERROR');
const errors = allErrors.filter((f) => inScope(f.rel));
const outOfScope = allErrors.filter((f) => !inScope(f.rel));
const warns = findings.filter((f) => f.severity === 'WARN');

const byRule = (list) => {
  const map = new Map();
  for (const f of list) map.set(f.rule, (map.get(f.rule) ?? 0) + 1);
  return [...map.entries()].sort((a, b) => b[1] - a[1]);
};

function fmtList(list) {
  return list
    .sort((a, b) => a.rel.localeCompare(b.rel) || a.lineNo - b.lineNo)
    .map((f) => `  ${f.rel}:${f.lineNo}  [${f.rule}]  ${f.snippet}`)
    .join('\n');
}

const lines = [];
lines.push('디자인 토큰 이탈 검사 (절대값 금지 / 토큰만 사용)');
lines.push('='.repeat(60));
lines.push(`스캔 루트: ${projectRoot}`);
lines.push(
  `스캔 대상: **/*.{ts,tsx,css,html}  (토큰 정의 파일·자동 생성물 제외)`,
);
if (SCOPE.length) {
  lines.push(`적용 범위: ${SCOPE.join(', ')}  (범위 밖 이탈은 백로그로 집계)`);
}
lines.push(
  `ERROR ${errors.length}건 · WARN ${warns.length}건 · ds-allow 면제 ${allowlisted}건`,
);
lines.push('');
if (errors.length) {
  lines.push(`■ ERROR (authored 레이어 — 차단 대상) ${errors.length}건`);
  for (const [r, n] of byRule(errors))
    lines.push(`   - ${r}: ${n} — ${RULES[r]}`);
  lines.push('');
  lines.push(fmtList(errors));
  lines.push('');
}
if (warns.length) {
  lines.push(
    `▲ WARN (vendored 레이어 + v5 마이그레이션 — 추적/백로그) ${warns.length}건`,
  );
  for (const [r, n] of byRule(warns))
    lines.push(`   - ${r}: ${n} — ${RULES[r]}`);
  if (REPORT) {
    lines.push('');
    lines.push(fmtList(warns));
  } else {
    lines.push('   (전체 목록은 --report 로 확인)');
  }
  lines.push('');
}
if (outOfScope.length) {
  lines.push(
    `▣ 범위 밖 ERROR (아직 적용하지 않은 레이어 — 백로그) ${outOfScope.length}건`,
  );
  for (const [r, n] of byRule(outOfScope))
    lines.push(`   - ${r}: ${n} — ${RULES[r]}`);
  lines.push(
    '   이 숫자를 보고와 design-playbook.md "10. 프로젝트별 슬롯" 에 그대로 적는다.',
  );
  if (REPORT) {
    lines.push('');
    lines.push(fmtList(outOfScope));
  }
  lines.push('');
}
if (!errors.length && !warns.length && !outOfScope.length) {
  lines.push('✓ 이탈 없음 — 모든 시각 값이 토큰을 참조합니다.');
}

const out = lines.join('\n');
console.log(out);

if (REPORT) {
  const dir = join(projectRoot, 'test-results');
  await mkdir(dir, { recursive: true });
  await writeFile(
    join(dir, 'design-token-audit.md'),
    '```\n' + out + '\n```\n',
    'utf8',
  );
  console.log('\n→ test-results/design-token-audit.md 생성');
}

const fail = errors.length > 0 || (STRICT && warns.length > 0);
process.exit(fail ? 1 : 0);
