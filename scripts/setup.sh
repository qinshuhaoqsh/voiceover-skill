#!/bin/bash
# 第一次在一台 Mac 上装千问配音环境。会下载：qwen-tts 及其依赖（PyTorch 等，约 1.6 GB）和
# Qwen/Qwen3-TTS-12Hz-0.6B-Base 模型（Hugging Face，约 2.4 GB，Apache-2.0）。下载前先征得用户同意。
# 全部装在 $WS/.tools/ 下，不动系统。需要工作区里已有 .tools/micromamba（explainroo 那套环境装好时就有）。
set -euo pipefail
WS="${WS:-$HOME/Code/haomeile-video}"; cd "$WS"
export MAMBA_ROOT_PREFIX="$WS/.tools/mamba"
[ -x .tools/qwen/bin/python ] || .tools/micromamba create -y -q -p "$WS/.tools/qwen" -c conda-forge python=3.12 pip
PIP_CACHE_DIR="$WS/.tools/pip-cache" .tools/qwen/bin/pip install -q -U qwen-tts soundfile
M="$WS/.tools/qwen-models/Qwen3-TTS-12Hz-0.6B-Base"
[ -f "$M/model.safetensors" ] || HF_HOME="$WS/.tools/hf-cache" HF_HUB_DISABLE_TELEMETRY=1 .tools/qwen/bin/python -I -c "from huggingface_hub import snapshot_download as d; d('Qwen/Qwen3-TTS-12Hz-0.6B-Base', local_dir='$M')"
grep -i '^license' "$M/README.md" || true
# 参考音：my-voice/ref.wav 是用户在录音页（studio.py）录的那句，这里只做降噪副本
[ -f my-voice/ref-denoised.wav ] || .tools/env/bin/ffmpeg -v error -y -i my-voice/ref.wav -af "highpass=f=80,afftdn=nr=18:nf=-38:tn=1,lowpass=f=11000" my-voice/ref-denoised.wav
echo 装好了
