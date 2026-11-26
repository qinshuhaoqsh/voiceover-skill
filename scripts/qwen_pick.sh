#!/bin/bash
# 每段用不同随机种子各生成一版，用语音识别（explainroo voice）打分，留下识别最准的一版。
# 用法：P=videos/xxx [TAKES=3] [WS=~/Code/haomeile-video] qwen_pick.sh [段名...]   不写段名 = 全部段
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export WS="${WS:-$HOME/Code/haomeile-video}"; cd "$WS"; . ./env.sh >/dev/null
P="${P:?请用 P=videos/项目名 指定项目}"; TAKES="${TAKES:-3}"
SC="$*"; [ -n "$SC" ] || SC=$(grep -oE '^## [a-z0-9_-]+' "$P/script.md" | cut -c4- | tr '\n' ' ')
mkdir -p "$P/assets/narration"
for k in $(seq 1 "$TAKES"); do
  d="videos/qvar$k"; rm -rf "$d"; mkdir -p "$d/assets/narration"; cp "$P/video.json" "$P/scenes.js" "$d/"
  python3 - "$P" "$d" $SC <<'PY'
import re, sys
P, d, keep = sys.argv[1], sys.argv[2], set(sys.argv[3:])
head, *parts = re.split(r'^## ', open(P + '/script.md').read(), flags=re.M)
open(d + '/script.md', 'w').write(head + ''.join('## ' + p for p in parts if p.split()[0] in keep))
PY
  SEED=$k P="$d" PYTORCH_ENABLE_MPS_FALLBACK=1 "$WS/.tools/qwen/bin/python" "$HERE/qwen_clone.py" project $SC 2>&1 | grep -vE 'pad_token_id|^\*+$' || true
  explainroo voice "$d" > "$d/voice.log" 2>&1 || true
done
python3 - "$P" "$TAKES" $SC <<'PY'
import json, shutil, sys
P, n, scenes = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
for sc in scenes:
    best = None
    for k in range(1, n + 1):
        try: j = json.load(open(f'videos/qvar{k}/build/voice/{sc}.json'))
        except FileNotFoundError: continue
        r = j.get('matchRate', 0); print(f'{sc} 第{k}版 {r:.2f}  {j["transcript"][:70]}')
        if best is None or r > best[0]: best = (r, k)
    if best:
        shutil.copy(f'videos/qvar{best[1]}/assets/narration/{sc}.wav', f'{P}/assets/narration/{sc}.wav'); print(f'选用 {sc}：第{best[1]}版 {best[0]:.2f}')
PY
for k in $(seq 1 "$TAKES"); do rm -rf "videos/qvar$k"; done
