#!/usr/bin/env python3
"""md 안의 ```mermaid 블록을 PNG로 렌더해 ![](png) 로 치환한다.

usage: _mermaid_to_img.py <in.md> <out.md> <imgdir> <mmdc_cmd_json> <mmconf> <puppeteer_json>
  mmdc_cmd_json: mmdc 실행 인자 배열(JSON). 예) ["npx","-y","-p","@mermaid-js/mermaid-cli","mmdc"]
렌더 실패 시 해당 블록은 원본 코드펜스로 그대로 둔다(전체 실패 대신 부분 보존).
"""
import sys, re, json, subprocess, pathlib

src, out, imgdir, mmdc_json, mmconf, pjson = sys.argv[1:7]
mmdc = json.loads(mmdc_json)
imgdir = pathlib.Path(imgdir); imgdir.mkdir(parents=True, exist_ok=True)
text = pathlib.Path(src).read_text(encoding="utf-8")

pat = re.compile(r"```mermaid[ \t]*\n(.*?)\n```", re.S)
idx = 0
def render(m):
    global idx
    idx += 1
    code = m.group(1)
    mmd = imgdir / f"diagram_{idx}.mmd"
    png = imgdir / f"diagram_{idx}.png"
    mmd.write_text(code + "\n", encoding="utf-8")
    cmd = mmdc + ["-i", str(mmd), "-o", str(png),
                  "-c", mmconf, "-p", pjson, "-b", "white", "-s", "2"]
    last = ""
    for attempt in range(1, 3):  # chrome 콜드스타트 대비 최대 2회 재시도
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
            return f"![]({png.resolve()})"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            last = getattr(e, "stderr", "") or str(e)
            sys.stderr.write(f"[mermaid] diagram_{idx} 시도 {attempt} 실패\n")
    sys.stderr.write(f"[mermaid] diagram_{idx} 렌더 실패, 원본 유지:\n{last[-500:]}\n")
    return m.group(0)

new = pat.sub(render, text)
pathlib.Path(out).write_text(new, encoding="utf-8")
sys.stderr.write(f"[mermaid] {idx}개 블록 처리\n")
