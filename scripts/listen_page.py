"""做一个本机试听页：音频直接嵌进 HTML（应用右侧的预览面板只显示静态快照、加载不了旁边的音频文件），用 Chrome 打开。
用法：python3 listen_page.py spec.json 输出.html
spec.json: {"title": "...", "lead": "...", "sections": [{"title": "第 1 句", "text": "原句", "items": [{"label": "版本名", "sub": "一句说明", "file": "a.wav"}]}]}
文件路径相对 spec.json 所在目录。需要 ffmpeg 在 PATH 上（工作区 env.sh 提供）。"""
import base64, html, json, os, subprocess, sys, tempfile

spec_path, out = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path)); tmp = tempfile.mkdtemp()
def emb(f):
    o = os.path.join(tmp, f'{abs(hash(f))}.m4a')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(base, f), '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', o], check=True)
    return 'data:audio/mp4;base64,' + base64.b64encode(open(o, 'rb').read()).decode()
e = html.escape
secs = ''
for s in spec['sections']:
    rows = ''.join(f'<div class="row"><div class="tag">{e(i["label"])}<small>{e(i.get("sub", ""))}</small></div><audio controls preload="metadata" src="{emb(i["file"])}"></audio></div>' for i in s['items'])
    secs += f'<section><div class="no">{e(s.get("title", ""))}</div><div class="text">{e(s.get("text", ""))}</div>{rows}</section>\n'
page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(spec["title"])}</title>
<style>:root{{--bg:#f6f5f2;--card:#fff;--ink:#1d1f23;--muted:#6b7078;--line:#e3e1dc;--a:#1f6feb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#131417;--card:#1c1e22;--ink:#eceef2;--muted:#9aa0aa;--line:#2b2e34;--a:#5ea2ff}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,"PingFang SC","Noto Sans SC",sans-serif}}
main{{max-width:760px;margin:0 auto;padding:28px 16px 60px}}h1{{font-size:24px;margin:0 0 6px}}.lead{{color:var(--muted);margin:0 0 24px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:0 0 18px}}
.no{{font-size:13px;color:var(--muted);font-weight:600}}.text{{font-size:18px;font-weight:600;margin:4px 0 14px}}
.row{{display:grid;grid-template-columns:200px 1fr;gap:10px;align-items:center;padding:8px 0;border-top:1px dashed var(--line)}}
.tag{{font-weight:700;color:var(--a)}}.tag small{{display:block;font-weight:500;color:var(--muted);font-size:12px;line-height:1.4}}audio{{width:100%}}
@media (max-width:560px){{.row{{grid-template-columns:1fr;gap:4px}}}}</style></head><body><main>
<h1>{e(spec["title"])}</h1><p class="lead">{e(spec.get("lead", ""))}</p>
{secs}</main><script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{{if(b!==a)b.pause()}})));</script></body></html>'''
open(out, 'w').write(page); print(out, f'{len(page) / 1e6:.2f} MB')
