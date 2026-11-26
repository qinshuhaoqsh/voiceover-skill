# voiceover（配音）skill

给 Claude Code 用的 skill：用自己的克隆声音给中文科普短视频配音。

- 声音模型：[Qwen3-TTS-12Hz-0.6B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)（Apache-2.0），只学音色，读音用标准普通话。
- 在 Mac 本机运行（Apple GPU / MPS），录音不离开电脑。
- 配合 [explainroo](https://www.explainroo.com/) 出片。

用法见 [SKILL.md](SKILL.md)。本仓库只有脚本和说明，不含任何录音、模型或生成的音频。

安装为个人 skill：

```bash
ln -s "$PWD" ~/.claude/skills/voiceover
```
