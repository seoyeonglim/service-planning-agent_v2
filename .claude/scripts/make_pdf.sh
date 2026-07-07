#!/usr/bin/env bash
# 공통 PDF 생성: md → (mermaid 블록을 PNG로 치환) → pandoc(+style.html 주입) → weasyprint
#
#   .claude/scripts/make_pdf.sh <입력.md> <출력.pdf> "[문서 제목]"
#
# 색 표준은 .claude/assets/pdf/{style.html, mermaid.json}, 설명은 PALETTE.md 참조.
# 사전: brew install pandoc weasyprint  (mermaid 렌더는 node/npx + puppeteer chrome 자동 사용)
set -euo pipefail

usage() { echo "Usage: make_pdf.sh <input.md> <output.pdf> [pagetitle]" >&2; exit 1; }
[ $# -ge 2 ] || usage
IN="$1"; OUT="$2"; TITLE="${3:-문서}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"          # .claude/
ASSETS="$ROOT/assets/pdf"
STYLE="$ASSETS/style.html"
MMCONF="$ASSETS/mermaid.json"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export npm_config_cache="${npm_config_cache:-$WORK/.npmcache}"

# puppeteer용 chrome 자동 탐지 (없으면 chrome-headless-shell 설치)
find_chrome() {
  local c
  for c in \
    "$HOME"/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell \
    "$HOME"/.cache/puppeteer/chrome/*/chrome-*/Google\ Chrome\ for\ Testing.app/Contents/MacOS/Google\ Chrome\ for\ Testing \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    [ -x "$c" ] && { printf '%s' "$c"; return 0; }
  done
  return 1
}
if ! CHROME="$(find_chrome)"; then
  echo "[make_pdf] chrome 미탐지 → chrome-headless-shell 설치" >&2
  npx -y puppeteer browsers install chrome-headless-shell >&2
  CHROME="$(find_chrome)" || { echo "[make_pdf] chrome 설치 실패 — mermaid 렌더 불가" >&2; exit 2; }
fi

PJSON="$WORK/puppeteer.json"
python3 -c 'import json,sys; print(json.dumps({"executablePath": sys.argv[1], "args":["--no-sandbox","--disable-setuid-sandbox"]}))' "$CHROME" > "$PJSON"

# 1) mermaid 블록 → PNG 치환
PROC="$WORK/proc.md"
MMDC_JSON='["npx","-y","-p","@mermaid-js/mermaid-cli","mmdc"]'
python3 "$HERE/_mermaid_to_img.py" "$IN" "$PROC" "$WORK/img" "$MMDC_JSON" "$MMCONF" "$PJSON"

# 2) pandoc → HTML (style.html 주입)
HTML="$WORK/doc.html"
pandoc "$PROC" -f gfm -t html5 -s \
  --metadata pagetitle="$TITLE" \
  --include-in-header="$STYLE" \
  -o "$HTML" 2>&1 | grep -viE 'text-rendering|max-width' || true

# 3) weasyprint → PDF
weasyprint "$HTML" "$OUT" 2>&1 | grep -viE 'text-rendering|max-width|@media|overflow' || true

echo "[make_pdf] 생성 완료: $OUT" >&2
