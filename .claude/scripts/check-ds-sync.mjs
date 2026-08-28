#!/usr/bin/env node
/**
 * 정본 문서 드리프트 검사 — **소비 레포에서 도는 게이트**.
 *
 * 이 레포의 거버넌스 문서는 소비 레포로 복사돼 쓰인다. 복사본은 받는 순간부터 낡는데,
 * 낡았다는 사실을 아무도 모른 채 소비 레포의 `check:design` 과 `/design-review` 가
 * **낡은 기준으로 통과 판정**을 내린다. 게이트가 낡은 자를 들고 재는 상태다.
 *
 * 이 스크립트는 그 하나만 본다 — 내가 가진 사본이 정본의 현재 상태와 같은가.
 *
 *   사본 stamp:  > ⤳ vendored from <repo> @ <commit> · doc-sha a3f2c1d0e5b7 · ...
 *   정본 manifest: { "path": "docs/design-playbook.md", "sha": "a3f2c1d0e5b7" }
 *
 * **사본을 다시 해싱해 비교하지 않는다.** 사본에는 stamp 가 붙고 playbook 은
 * "10. 프로젝트별 슬롯" 을 각 레포가 채우므로 정본과 내용이 반드시 달라진다.
 * 비교 대상은 어디까지나 stamp 에 적어 둔 `doc-sha` 다.
 *
 * 사용:
 *   node scripts/check-ds-sync.mjs                       -- 낡은 문서 있으면 exit 1
 *   node scripts/check-ds-sync.mjs --manifest <url>      -- manifest 주소 지정
 *   node scripts/check-ds-sync.mjs --strict              -- 판정 불가(WARN)도 실패로 취급
 *
 * manifest 주소는 `--manifest` 로 준다. CI 에는 걸지 않는다 — 정본 배포가 로그인
 * 뒤에 있어 CI 가 manifest 를 받지 못한다. 드리프트가 의심될 때 수동으로 실행하는
 * 도구다. 주소가 없으면 검사를 건너뛰고 경고만 남긴다.
 */

// ─────────────────────────────────────────────────────────────────────────
// [로컬 패치 — service-planning-agent 워크플로우 레포]
//   정본 manifest 의 경로는 `docs/design-playbook.md` 형태다. 이 레포는 사본을
//   `.claude/design-system/` 에 둔다(이 레포의 `docs/` 는 고객 산출물이라 통째로
//   git 추적 제외 — 사유는 design-playbook.md "10. 프로젝트별 슬롯").
//   패치하지 않으면 모든 사본이 "manifest 범위 밖" 으로 빠져 **한 건도 대조되지
//   않은 채 통과**한다 — 게이트가 꺼진 줄 모르는 상태가 된다.
//   그래서 1가지만 로컬 패치했다 (대조 로직·판정 기준은 무수정):
//     ① 사본 경로 `design-system/**` 를 manifest 경로 `docs/**` 로 정규화
//   ⚠️ 정본 재동기화 시 이 패치를 재적용해야 한다.
// ─────────────────────────────────────────────────────────────────────────

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const ROOT = resolve(import.meta.dirname, '..');
const argv = process.argv.slice(2);
const STRICT = argv.includes('--strict');
const manifestFlagAt = argv.indexOf('--manifest');
const MANIFEST_URL =
  manifestFlagAt === -1 ? undefined : argv[manifestFlagAt + 1];

const SKIP_DIRS = new Set([
  'node_modules',
  '.next',
  '.git',
  'dist',
  'build',
  'coverage',
  '.omc',
  '.omx',
]);

/** `> ⤳ vendored from <repo> @ <commit> · doc-sha <sha> · ...` — 뒤쪽 꼬리만 캡처한다. */
const STAMP_RE = /^>\s*⤳\s*vendored from\s+\S+\s+@\s+\S+([^\n]*)$/m;
/* 최소 길이는 `shaMatches` 의 8자와 맞춘다. 더 짧은 값을 받아들이면 비교기가
   전부 "낡음" 으로 떨어뜨려, 최신 문서인데 영원히 FAIL 하는 오탐이 된다.
   여기서 걸러내면 "doc-sha 없음 → 판정 불가 WARN" 이라는 옳은 메시지로 간다. */
const DOC_SHA_RE = /·\s*doc-sha\s+([0-9a-f]{8,64})\b/;

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    if (SKIP_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    // 깨진 심링크에서 throw 하지 않는다 — 남의 레포에서 도는 스크립트가 문서
    // 드리프트와 무관한 파일시스템 상태로 검사를 깨면 안 된다.
    const stat = statSync(full, { throwIfNoEntry: false });
    if (!stat) continue;
    if (stat.isDirectory()) walk(full, out);
    else if (entry.endsWith('.md')) out.push(full);
  }
  return out;
}

/**
 * stamp 의 doc-sha 와 정본 sha 를 견준다. 길이가 다를 수 있어 프리픽스로 본다 —
 * 정본은 12자를 싣지만 사본을 만들 때 `cut -c1-16` 처럼 다른 길이로 잘라 적는 일이
 * 실제로 생긴다. 길이가 달라 "영원히 낡음" 으로 뜨면 게이트를 꺼버리게 된다.
 */
function shaMatches(docSha, upstreamSha) {
  const short = docSha.length <= upstreamSha.length ? docSha : upstreamSha;
  const long = docSha.length <= upstreamSha.length ? upstreamSha : docSha;
  return short.length >= 8 && long.startsWith(short);
}

/** stamp 가 달린 파일만 추린다. stamp 가 없으면 vendored 문서가 아니다. */
function collectStamped() {
  const found = [];
  for (const absolute of walk(ROOT)) {
    const stamp = readFileSync(absolute, 'utf8').match(STAMP_RE);
    if (!stamp) continue;
    found.push({
      // [로컬 패치 ①] `design-system/x.md` → `docs/x.md` 로 manifest 경로에 맞춘다.
      path: relative(ROOT, absolute).replace(/^design-system\//, 'docs/'),
      docSha: stamp[1].match(DOC_SHA_RE)?.[1] ?? null,
    });
  }
  return found;
}

async function main() {
  const stamped = collectStamped();

  if (stamped.length === 0) {
    console.log(
      'vendored 문서가 없습니다 — 이 레포가 정본이거나 아직 디자인 시스템을 도입하지 않았습니다.',
    );
    return 0;
  }

  if (!MANIFEST_URL) {
    console.warn(
      `WARN  manifest 주소가 없어 ${stamped.length}개 vendored 문서를 검사하지 못했습니다.`,
    );
    console.warn(
      '      --manifest <url> 로 정본의 /llms/manifest.json 주소를 지정하세요.',
    );
    console.warn('      지정 전까지 문서 드리프트 가드레일은 꺼진 상태입니다.');
    return STRICT ? 1 : 0;
  }

  let manifest;
  try {
    const response = await fetch(MANIFEST_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    manifest = await response.json();
    // 주소를 잘못 걸면 200 + HTML 이 오는 호스트가 있다. 형태를 확인하지 않으면
    // 게이트가 꺼진 채로 통과 판정만 남는다.
    if (!Array.isArray(manifest?.docs)) {
      throw new Error(
        'docs 배열이 없습니다 — manifest 주소가 맞는지 확인하세요',
      );
    }
  } catch (error) {
    console.warn(
      `WARN  manifest 를 받지 못했습니다 (${MANIFEST_URL}) — ${error.message}`,
    );
    console.warn('      네트워크나 배포 상태를 확인하세요. 검사를 건너뜁니다.');
    return STRICT ? 1 : 0;
  }

  const byPath = new Map(manifest.docs.map((doc) => [doc.path, doc]));
  const stale = [];
  const unstamped = [];
  const outOfScope = [];

  for (const doc of stamped) {
    const upstream = byPath.get(doc.path);
    if (!upstream) {
      outOfScope.push(doc);
      continue;
    }
    if (!doc.docSha) {
      unstamped.push(doc);
      continue;
    }
    if (!shaMatches(doc.docSha, upstream.sha)) {
      stale.push({ ...doc, upstream });
    }
  }

  const judged = stamped.length - outOfScope.length;
  console.log(
    `정본 ${manifest.name} @ ${manifest.version} 기준으로 대조했습니다.`,
  );
  console.log(
    `검사 대상 ${judged}건 · 최신 ${judged - stale.length - unstamped.length}건\n`,
  );

  for (const doc of stale) {
    console.error(`FAIL  ${doc.path} 가 낡았습니다.`);
    console.error(
      `      사본 doc-sha ${doc.docSha} · 정본 sha ${doc.upstream.sha}`,
    );
    let where = doc.upstream.url;
    try {
      where = new URL(doc.upstream.url, MANIFEST_URL).href;
    } catch {
      // 주소를 못 만들어도 리포트를 끊지 않는다 — 아래 재동기화 안내가 본체다.
    }
    console.error(`      다시 받기: ${where}`);
  }

  for (const doc of unstamped) {
    console.warn(
      `WARN  ${doc.path} 의 stamp 에 doc-sha 가 없어 판정할 수 없습니다.`,
    );
    console.warn('      재동기화 후 stamp 를 새 형식으로 갱신하세요.');
  }

  /* 범위 밖은 위반이 아니라 설계다 — manifest 는 `docs/` 만 담고, vendoring 되는
     `.claude/commands/` 에도 stamp 가 붙는다. 이걸 WARN 으로 내면 모든 소비 레포가
     매 실행마다 같은 경고를 받고, 그만큼 WARN 이라는 신호가 죽는다. 한 줄로 알린다. */
  if (outOfScope.length > 0) {
    console.log(
      `참고  manifest 범위(docs/) 밖 ${outOfScope.length}건은 대조하지 않았습니다 — ${outOfScope.map((d) => d.path).join(', ')}`,
    );
  }

  if (stale.length > 0) {
    console.error(
      `\n낡은 문서 ${stale.length}건. \`/setup-design-system --mode brownfield\` 로 재동기화하세요.`,
    );
    console.error(
      '낡은 규칙 위에서 통과한 design-review 결과는 근거가 없습니다.',
    );
    return 1;
  }

  if (STRICT && unstamped.length > 0) return 1;

  console.log(
    unstamped.length > 0
      ? `낡은 문서는 없습니다. 다만 ${unstamped.length}건은 판정하지 못했습니다 (위 WARN).`
      : '대조한 문서가 모두 정본과 같습니다.',
  );
  return 0;
}

main().then(
  (code) => process.exit(code),
  (error) => {
    console.error(`검사 중 오류: ${error.message}`);
    process.exit(1);
  },
);
