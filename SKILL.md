---
name: voiceover
description: 用用户自己的克隆声音给中文科普短视频配音（千问 Qwen3-TTS，只学音色、标准普通话播音腔，本机运行）。用户说“配音”“用我的声音念”“生成口播”“重新配音”“换声音”，或在 ~/Code/haomeile-video 里做视频需要旁白时使用。也管配音试听对比页和背景音乐/音效的音量。
---

# 配音（克隆声音）

用户已认可的做法（2026-11-26 定）：**千问 Qwen3-TTS-12Hz-0.6B-Base，只学音色**——从用户参考录音里只取音色，读音和语调用模型自己的标准普通话（要更像播音腔）。全部在本机跑，录音不出这台电脑。

工作区默认 `~/Code/haomeile-video`（`WS` 可改）。本 skill 的脚本在 `scripts/`：

| 脚本 | 做什么 |
|---|---|
| `setup.sh` | 第一次装环境和模型（会下载约 4 GB，**先问用户**） |
| `qwen_clone.py` | 念一个项目 `script.md` 的每段，或试念几句 |
| `qwen_pick.sh` | 每段换随机种子生成几版，用语音识别打分，留最准的 |
| `listen_page.py` | 做一个音频嵌在里面的试听页，给用户逐个点着听 |

## 默认参数（用户选定，别擅自改）

- 参考音 `my-voice/ref-denoised.wav`：用户录音先降噪再用（原始 `ref.wav` 保留）。参考文本必须和录音一字不差：“大家好，今天聊聊我平时怎么用 AI 写代码，顺便说说踩过的坑。”
- `XVEC=1` 只学音色；`SPEED=1.3`（ffmpeg atempo，接近用户认可的节奏）；生成后 ffmpeg 降噪。
- 生成前自动去掉中英文之间的空格：空格会被念成小停顿（“所有人的 Gemini 额度”Gemini 前后会卡）。英文词之间的空格保留。
- 英文照念，不要音译、不要为了好念删掉英文。千问按语境读多音字和数字，`{显示|读法}` 里它用**显示**那一半；字幕也用显示。

## 流程

1. **稿子**：项目 `videos/<名>/script.md`，每段 `## 段名`（小写英文），口播里用 `[#标记]` 给画面对时间。数字可写 `{10529 点|一万零五百二十九点}` 让字幕显示阿拉伯数字。
2. **生成**（单段约 3 秒算 1 秒音频，在 Mac 的 GPU 上）：
   ```bash
   cd ~/Code/haomeile-video && P=videos/<名> PYTORCH_ENABLE_MPS_FALLBACK=1 .tools/qwen/bin/python <skill>/scripts/qwen_clone.py project
   ```
   同一段同一文字有缓存；要重来用 `FRESH=1` 或换 `SEED`。
3. **检查**：`. ./env.sh && explainroo voice videos/<名>`，看每段 `% confirmed` 和 `build/voice/<段>.json` 的 `transcript`。识别是中文模式，英文常被写成怪字（Gemini 听成“兼赖”）——那不一定是读错，以用户耳朵为准。识别明显不对、或有卡顿的段，用：
   ```bash
   P=videos/<名> TAKES=3 <skill>/scripts/qwen_pick.sh 段名 段名
   ```
4. **让用户听**：别只靠识别分。用 `listen_page.py` 做试听页，`open -a "Google Chrome 2" 页面.html`（这台 Mac 的 Chrome 叫 “Google Chrome 2”）。**不要**用应用右侧的预览面板放本机音频：它把本地页面显示成静态快照，旁边的音频文件加载不进来。
5. 用户点头后再渲染视频（explainroo 的 `use-recording.sh --ready`，见工作区记录）。

## 背景音乐与音效

- explainroo 的内置音乐：`calm` 没有鼓；`upbeat` 轻鼓；`tech` 稳定底鼓。用户要听得见鼓点。
- explainroo 说话时自动把音乐压低 8 dB，加上音量偏低，鼓点会被埋掉。本机那份 explainroo 改过 `engine/audio/soundtrack.js`：从同目录 `mix.json` 读 `{"duckDb": -3, "musicGain": 1, "sfxGain": 1.6}`，没有这个文件就和原版一样。`video.json` 里 `music.volume` 最大 1。
- **用户选定的混音（2026-11-26）**：`video.json` 里 `"music": {"style": "upbeat", "volume": 1.0}`（要听得见鼓点，别用没有鼓的 `calm`）；`mix.json` 为 `{"duckDb": -3, "musicGain": 1, "sfxGain": 1.6}`，即说话时音乐只压低 3 dB、音效加大 1.6 倍。新项目照这个设。
- 换电脑或重装 explainroo 后，这个改动会丢：在 `engine/audio/soundtrack.js` 里把 `DUCK_DB`、音乐 `volume`、`scheduleSfx` 的 `volume` 分别乘上 `mix.json` 的三个值，再放好 `mix.json`。

## 注意

- 用户的录音和克隆声音是隐私：不上传、不放进公开的页面或仓库。
- 旧方案 ZipVoice（`gen_voice.py`、`pick_voice.sh`）的模型权重是 CC-BY-NC（非商业），已弃用；千问是 Apache-2.0。
- 下载任何新模型或依赖前，先告诉用户文件名、来源、大小，等用户同意。
