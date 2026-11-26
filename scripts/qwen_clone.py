"""本机声音克隆配音：Qwen3-TTS-12Hz-0.6B-Base（Apache-2.0），只学音色、标准普通话。
用法（在工作区里运行，工作区默认 ~/Code/haomeile-video，可用 WS 指定）：
  $WS/.tools/qwen/bin/python qwen_clone.py test 输出目录 "句子1" "句子2" ...
  P=videos/xxx $WS/.tools/qwen/bin/python qwen_clone.py project [段名...]   # 念 P/script.md 每段 -> P/assets/narration/段名.wav
环境变量：
  WS     工作区（放 .tools/、my-voice/、videos/）
  REF    参考音，默认 my-voice/ref-denoised.wav（先降噪过的参考录音）
  XVEC   1=只学音色，读音和语调用标准普通话（默认）；0=连口音一起学
  SPEED  语速，ffmpeg atempo，默认 1.3
  SEED   随机种子，默认 0；换种子就是换一版
  FRESH  1=忽略缓存重新生成
  DEVICE mps|cpu，默认有 mps 就用"""
import os, re, sys, time, hashlib, subprocess
import numpy as np, soundfile as sf, torch
from qwen_tts import Qwen3TTSModel

WS = os.path.expanduser(os.environ.get('WS', '~/Code/haomeile-video')); os.chdir(WS)
MODEL = WS + '/.tools/qwen-models/Qwen3-TTS-12Hz-0.6B-Base'
REF = os.environ.get('REF', WS + '/my-voice/ref-denoised.wav')
REF_TEXT = os.environ.get('REF_TEXT', '大家好，今天聊聊我平时怎么用 AI 写代码，顺便说说踩过的坑。')
FFMPEG = WS + '/.tools/env/bin/ffmpeg'
XVEC = os.environ.get('XVEC', '1') == '1'
SEED = int(os.environ.get('SEED', '0'))
DENOISE = 'highpass=f=80,afftdn=nr=18:nf=-38:tn=1,lowpass=f=11000'

def load():
    dev = os.environ.get('DEVICE', 'mps' if torch.backends.mps.is_available() else 'cpu')
    dtype = torch.float32 if dev == 'cpu' else torch.bfloat16
    t = time.time()
    m = Qwen3TTSModel.from_pretrained(MODEL, device_map=dev, dtype=dtype, attn_implementation='sdpa')
    print(f'loaded on {dev} ({dtype}) in {time.time() - t:.1f}s', flush=True)
    return m

def tidy(text):
    # 中英文之间的空格会被念成小停顿（“所有人的 Gemini 额度”会在 Gemini 前后卡一下），去掉；英文词之间的空格保留
    text = re.sub(r'(?<=[一-鿿，。！？、：；])\s+(?=[A-Za-z0-9])', '', text)
    return re.sub(r'(?<=[A-Za-z0-9%])\s+(?=[一-鿿，。！？、：；])', '', text)

_prompt = None
def speak(m, text):
    global _prompt
    text = tidy(text)
    if _prompt is None: _prompt = m.create_voice_clone_prompt(ref_audio=REF, ref_text=REF_TEXT, x_vector_only_mode=XVEC)
    out, sr = [], None
    for i, s in enumerate(p.strip() for p in re.split(r'(?<=[。！？])', text) if p.strip()):
        torch.manual_seed(SEED * 1000 + i)
        wavs, sr = m.generate_voice_clone(text=s, language='Chinese', voice_clone_prompt=_prompt)
        out += [np.zeros(int(sr * 0.3), np.float32)] if out else []
        out.append(np.asarray(wavs[0], dtype=np.float32))
    return np.concatenate(out), sr

def script_parts(P):
    for b in re.split(r'^## ', open(P + '/script.md').read(), flags=re.M)[1:]:
        h, *ls = b.split('\n'); t = ''.join(l for l in ls if l.strip() and not l.startswith('>'))
        t = re.sub(r'\[[^\]]*\]', '', t)
        t = re.sub(r'\{([^|}]*)\|[^}]*\}', r'\1', t)  # Qwen 按语境读多音字和数字：{显示|读法} 取显示
        yield h.split()[0], t

if __name__ == '__main__':
    mode = sys.argv[1]; m = load()
    if mode == 'test':
        d = sys.argv[2]; os.makedirs(d, exist_ok=True)
        for i, s in enumerate(sys.argv[3:], 1):
            t = time.time(); w, sr = speak(m, s); sf.write(f'{d}/qwen-{i}.wav', w, sr)
            print(f'{i}: {len(w) / sr:.1f}s audio in {time.time() - t:.1f}s  {s}', flush=True)
    else:
        P = os.environ['P']; only = set(sys.argv[2:]); speed = os.environ.get('SPEED', '1.3')
        os.makedirs(P + '/assets/narration', exist_ok=True); os.makedirs('my-voice/qwen-cache', exist_ok=True)
        for sid, text in script_parts(P):
            if only and sid not in only: continue
            key = hashlib.sha256(open(REF, 'rb').read() + tidy(text).encode() + f'{XVEC}|{SEED}'.encode()).hexdigest()[:16]
            raw = f'my-voice/qwen-cache/{sid}-{key}.wav'; t = time.time()
            if os.environ.get('FRESH') == '1' or not os.path.exists(raw): w, sr = speak(m, text); sf.write(raw, w, sr)
            subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', raw, '-af', f'atempo={speed},' + DENOISE, f'{P}/assets/narration/{sid}.wav'], check=True)
            print(sid, f'{time.time() - t:.1f}s', flush=True)
