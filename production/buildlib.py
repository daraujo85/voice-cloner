#!/usr/bin/env python3
"""Base reutilizável de produção de vídeo-aula (tema escuro Garagem do Código).
Componentes: geradores de gráfico (corrigidos: listas, centralização vertical),
terminal simulado, slide() (foto | gráfico | clipe de vídeo), e render por segmentos
com composição de clipes (captura de navegador etc.). Import por cada build de aula."""
import json, os, base64, subprocess, unicodedata, random

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GEN = os.path.expanduser("~/.claude/skills/gerar-imagem-web/gen.sh")
CAPWEB = os.path.expanduser("~/.claude/skills/capturar-web/capweb.js")

BG = "#12100b"; PANEL = "#1b1811"; INK = "#f3f1ea"; MUT = "#b4afa3"
GREEN = "#8fd45f"; GREEN_D = "#3f7a1f"; RED = "#e0796f"; AMBER = "#e8b06a"; BLUE = "#7fb0e8"; VIOLET = "#b79be0"
STYLE = "foto realista, luz natural, alta qualidade, 16:9, sem texto legível na imagem. "
FX, FY, FW, FH = 280, 175, 1360, 765  # moldura de vídeo (fundo do slide + overlay ffmpeg)

random.seed(7)
STARS = "".join(f'<circle cx="{random.randint(0,1920)}" cy="{random.randint(0,1080)}" r="{random.choice([1,1,1,2])}" fill="#fff" opacity="{random.choice([.12,.2,.35,.45])}"/>' for _ in range(120))


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

def _load_norm_rules():
    # Usa a MESMA normalização determinística do transcript_tools (norm.json),
    # pra âncora casar com o transcript normalizado (ex.: "tmux" ↔ "TMOOX").
    try:
        import textnorm
        return textnorm, textnorm.load_rules()
    except Exception:
        return None, None

def make_find_time(SEGS):
    # Casa a âncora na transcrição JUNTA (cross-segment): a frase pode estar partida
    # entre vários segmentos curtos. Aplica a normalização de termos (norm.json) +
    # deacento/minúsculas, e mapeia cada char ao start time do segmento.
    tn, rules = _load_norm_rules()
    def key(s):
        return tn.normalize_and_key(s, rules) if tn else norm(s)
    segs = [s for s in SEGS if s["text"].strip()]
    full = ""
    starts = []  # start time por caractere
    for s in segs:
        t = key(s["text"]) + " "
        full += t
        starts.extend([s["start"]] * len(t))
    def find_time(anchor):
        pos = full.find(key(anchor))
        return starts[pos] if pos >= 0 else None
    return find_time

def generate(art_dir, art_id, prompt, autojudge=True):
    out = os.path.join(art_dir, art_id + ".png")
    if os.path.exists(out) and os.path.getsize(out) > 3000:
        return out
    print("  gerando:", art_id, flush=True)
    args = ["bash", GEN, "gemini", STYLE + prompt, out]
    if autojudge:
        args.append("--autojudge")
    subprocess.run(args, capture_output=True, text=True)
    return out if (os.path.exists(out) and os.path.getsize(out) > 3000) else None


# ---------------- geradores de GRÁFICO (HTML do miolo) ----------------
def _dot(c):
    return f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{c};margin:10px 18px 0 0;flex:none"></span>'

def g_statement(big, sub=""):
    return f'''<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:30px">
      <div style="font-size:118px;font-weight:900;color:{INK};letter-spacing:-3px;line-height:1.02;text-align:center">{big}</div>
      {f'<div style="font-size:42px;color:{MUT};max-width:1250px;text-align:center;line-height:1.3">{sub}</div>' if sub else ''}</div>'''

def g_flow(items):
    # items: (label, descrição, exemplo?)
    cells = ""
    for i, it in enumerate(items):
        lb, ds, ex = (list(it) + ["", ""])[:3]
        exhtml = (f'<div style="width:44px;height:2px;background:{GREEN_D};margin:6px 0 2px"></div>'
                  f'<div style="color:{GREEN};font-family:ui-monospace,monospace;font-size:18px;letter-spacing:.12em;text-transform:uppercase">exemplo</div>'
                  f'<div style="color:{INK};font-size:26px;line-height:1.35;font-style:italic;opacity:.92">{ex}</div>') if ex else ''
        cells += f'''<div style="flex:1;background:{PANEL};border:1px solid {GREEN_D};border-radius:24px;padding:40px 28px;display:flex;flex-direction:column;align-items:center;justify-content:{'flex-start' if ex else 'center'};gap:16px;min-height:{560 if ex else 420}px">
          <div style="width:58px;height:58px;border-radius:50%;background:rgba(143,212,95,.12);border:2px solid {GREEN};display:flex;align-items:center;justify-content:center;color:{GREEN};font-family:ui-monospace,monospace;font-size:28px;font-weight:800;flex:none">{i+1}</div>
          <div style="color:{INK};font-size:40px;font-weight:800">{lb}</div>
          <div style="color:{MUT};font-size:25px;line-height:1.3">{ds}</div>{exhtml}</div>'''
        if i < len(items)-1:
            cells += f'<div style="align-self:center;color:{GREEN};font-size:48px;font-weight:800;flex:none">&rarr;</div>'
    return f'<div style="display:flex;align-items:center;justify-content:center;gap:18px;height:100%">{cells}</div>'

def g_compare(lt, li, rt, ri, lc=AMBER, rc=GREEN):
    def col(t, items, c):
        rows = "".join(f'<div style="display:flex;align-items:flex-start;margin:16px 0;color:{INK};font-size:34px;line-height:1.35;text-align:left">{_dot(c)}<span>{x}</span></div>' for x in items)
        return f'''<div style="flex:1;background:{PANEL};border-radius:24px;border-top:5px solid {c};padding:48px 54px;display:flex;flex-direction:column;justify-content:center;min-height:520px">
          <div style="color:{c};font-size:46px;font-weight:900;margin-bottom:26px;text-align:center">{t}</div>{rows}</div>'''
    return f'<div style="display:flex;gap:40px;height:100%;align-items:center;justify-content:center">{col(lt,li,lc)}{col(rt,ri,rc)}</div>'

def g_beforeafter(bt, btxt, gt, gtxt, lc=RED, rc=GREEN):
    def card(t, txt, c):
        return f'''<div style="flex:1;background:{PANEL};border-radius:24px;border:1px solid {c};padding:52px 50px;display:flex;flex-direction:column;justify-content:center;gap:24px;min-height:420px">
          <div style="color:{c};font-size:44px;font-weight:900;text-align:center">{t}</div>
          <div style="color:{INK};font-size:35px;line-height:1.45;font-style:italic;text-align:center">&ldquo;{txt}&rdquo;</div></div>'''
    return f'<div style="display:flex;gap:40px;height:100%;align-items:center;justify-content:center">{card(bt,btxt,lc)}{card(gt,gtxt,rc)}</div>'

def g_single(title, txt, c=GREEN):
    return f'''<div style="display:flex;align-items:center;justify-content:center;height:100%">
      <div style="background:{PANEL};border:1px solid {c};border-radius:24px;padding:60px 72px;max-width:1250px;display:flex;flex-direction:column;gap:26px;align-items:center">
        <div style="color:{c};font-size:46px;font-weight:900;text-align:center">{title}</div>
        <div style="color:{INK};font-size:42px;line-height:1.4;font-style:italic;text-align:center">&ldquo;{txt}&rdquo;</div></div></div>'''

def g_cards(items):
    # grade de cartões-conceito: (título, descrição). 2 a 4 cartões.
    cells = "".join(f'''<div style="flex:1;background:{PANEL};border:1px solid rgba(143,212,95,.25);border-radius:22px;padding:44px 40px;display:flex;flex-direction:column;justify-content:center;gap:16px;min-height:420px">
      <div style="color:{GREEN};font-size:40px;font-weight:900">{t}</div>
      <div style="color:{INK};font-size:30px;line-height:1.4">{d}</div></div>''' for t, d in items)
    return f'<div style="display:flex;gap:34px;height:100%;align-items:center;justify-content:center">{cells}</div>'

def g_steps(labels, title=""):
    # pipeline de etapas numeradas em pílulas que quebram linha (bom p/ 6-9 passos).
    pills = ""
    for i, lb in enumerate(labels):
        pills += f'''<div style="display:flex;align-items:center;gap:14px">
          <div style="display:flex;align-items:center;gap:14px;background:{PANEL};border:1px solid {GREEN_D};border-radius:16px;padding:20px 28px">
            <span style="width:40px;height:40px;border-radius:50%;background:rgba(143,212,95,.14);border:2px solid {GREEN};display:flex;align-items:center;justify-content:center;color:{GREEN};font-family:ui-monospace,monospace;font-size:22px;font-weight:800">{i+1}</span>
            <span style="color:{INK};font-size:34px;font-weight:700">{lb}</span></div>
          {f'<span style="color:{GREEN};font-size:34px;font-weight:800">&rarr;</span>' if i<len(labels)-1 else ''}</div>'''
    # title ignorado de propósito: o kicker do slide já rotula a cena (evita header duplo).
    return f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%"><div style="display:flex;flex-wrap:wrap;gap:26px 16px;align-items:center;justify-content:center;max-width:1580px">{pills}</div></div>'

def g_terminal(lines, title="zsh — agente", tmux=None, prompt="➜"):
    """Terminal simulado. lines: lista de (kind, text). kind: prompt|out|ok|warn|dim|cmd."""
    body = ""
    for kind, txt in lines:
        if kind == "prompt":
            body += f'<div style="margin:3px 0"><span style="color:{GREEN}">{prompt}</span> <span style="color:{BLUE}">~</span> <span style="color:{INK}">{txt}</span></div>'
        elif kind == "cmd":
            body += f'<div style="margin:3px 0;color:{INK}">{txt}</div>'
        elif kind == "ok":
            body += f'<div style="margin:3px 0;color:{GREEN}">{txt}</div>'
        elif kind == "warn":
            body += f'<div style="margin:3px 0;color:{AMBER}">{txt}</div>'
        elif kind == "dim":
            body += f'<div style="margin:3px 0;color:{MUT}">{txt}</div>'
        else:
            body += f'<div style="margin:3px 0;color:#cfd3cc">{txt}</div>'
    if tmux is None:
        cursor = '<span style="display:inline-block;width:12px;height:24px;background:{};vertical-align:middle;margin-left:4px;animation:none"></span>'.format(GREEN)
        body += f'<div style="margin:3px 0"><span style="color:{GREEN}">{prompt}</span> <span style="color:{BLUE}">~</span> {cursor}</div>'
    statusbar = ""
    if tmux:
        statusbar = f'''<div style="position:absolute;left:0;right:0;bottom:0;height:38px;background:{GREEN_D};display:flex;align-items:center;justify-content:space-between;padding:0 20px;font-family:ui-monospace,Menlo,monospace;font-size:22px;color:#0f1f06">
          <span style="background:{GREEN};color:#0f1f06;padding:2px 14px;border-radius:4px;font-weight:800">{tmux}</span>
          <span style="color:#dff5cc">garagem · 1:agente 2:logs 3:testes</span></div>'''
    pad_bottom = 58 if tmux else 30
    return f'''<div style="width:1520px;height:700px;margin:0 auto;background:#0c0c0d;border-radius:16px;overflow:hidden;box-shadow:0 24px 70px rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.08);position:relative">
      <div style="height:46px;background:#1b1b1e;display:flex;align-items:center;padding:0 20px;gap:10px">
        <span style="width:14px;height:14px;border-radius:50%;background:#ff5f57"></span>
        <span style="width:14px;height:14px;border-radius:50%;background:#febc2e"></span>
        <span style="width:14px;height:14px;border-radius:50%;background:#28c840"></span>
        <span style="flex:1;text-align:center;color:{MUT};font-family:ui-monospace,Menlo,monospace;font-size:22px">{title}</span></div>
      <div style="padding:28px 34px {pad_bottom}px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:28px;line-height:1.5">{body}</div>
      {statusbar}</div>'''


def slide(kicker, title, visual, brand):
    if visual.get("clip"):
        return f'''<!doctype html><html><head><meta charset="utf-8"><style>*{{margin:0;box-sizing:border-box}}html,body{{width:1920px;height:1080px;overflow:hidden}}
        body{{background:{BG};font-family:-apple-system,"Segoe UI",Arial,sans-serif;position:relative}}</style></head><body>
        <svg style="position:absolute;inset:0" viewBox="0 0 1920 1080" preserveAspectRatio="none">{STARS}</svg>
        <div style="position:absolute;top:90px;left:0;right:0;text-align:center;font-family:ui-monospace,Menlo,monospace;color:{GREEN};font-size:24px;letter-spacing:.18em;text-transform:uppercase">{kicker}</div>
        <div style="position:absolute;left:{FX}px;top:{FY}px;width:{FW}px;height:{FH}px;border-radius:22px;background:#0d0b07;box-shadow:0 24px 70px rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.08)"></div>
        <div style="position:absolute;top:{FY+FH+26}px;left:0;right:0;text-align:center;color:{INK};font-size:44px;font-weight:800;line-height:1.14">{title}</div>
        <div style="position:absolute;left:64px;bottom:48px;font-family:ui-monospace,Menlo,monospace;color:{MUT};font-size:23px">{brand} <b style="color:{GREEN}">·</b> Garagem do Código</div>
        <div style="position:absolute;left:0;right:0;bottom:0;height:10px;background:linear-gradient(90deg,{GREEN_D},{GREEN})"></div>
        </body></html>'''
    if visual.get("img") and os.path.exists(visual["img"]):
        b64 = base64.b64encode(open(visual["img"], "rb").read()).decode()
        mid = f'<div style="width:1120px;height:600px;border-radius:22px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.06)"><img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;display:block"/></div>'
        cap = f'<div style="color:{INK};font-size:48px;font-weight:800;line-height:1.14;max-width:1500px;margin-top:28px;text-align:center">{title}</div>'
    else:
        mid = f'<div style="width:1640px;height:640px">{visual.get("graphic","")}</div>'
        cap = f'<div style="color:{MUT};font-size:34px;line-height:1.2;max-width:1500px;margin-top:16px;text-align:center">{title}</div>' if title else ''
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>*{{margin:0;box-sizing:border-box}}html,body{{width:1920px;height:1080px;overflow:hidden}}
    body{{background:{BG};font-family:-apple-system,"Segoe UI",Arial,sans-serif;position:relative}}</style></head><body>
    <svg style="position:absolute;inset:0" viewBox="0 0 1920 1080" preserveAspectRatio="none">{STARS}</svg>
    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:46px 120px;text-align:center">
      <div style="font-family:ui-monospace,Menlo,monospace;color:{GREEN};font-size:24px;letter-spacing:.18em;text-transform:uppercase;margin-bottom:18px">{kicker}</div>
      {mid}{cap}</div>
    <div style="position:absolute;left:64px;bottom:48px;font-family:ui-monospace,Menlo,monospace;color:{MUT};font-size:23px">{brand} <b style="color:{GREEN}">·</b> Garagem do Código</div>
    <div style="position:absolute;left:0;right:0;bottom:0;height:10px;background:linear-gradient(90deg,{GREEN_D},{GREEN})"></div>
    </body></html>'''


def probe_dur(path):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",path], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except Exception: return 0.0

def render_video(cues, audio, out, brand, frames_dir):
    """cues: [{start,end,dur,kicker,title,visual}]  (já ordenadas e com dur)."""
    os.makedirs(frames_dir, exist_ok=True)
    segdir = os.path.join(frames_dir, "seg"); os.makedirs(segdir, exist_ok=True)
    audio_end = max(c["end"] for c in cues)
    print("Renderizando slides + segmentos...", flush=True)
    for i, c in enumerate(cues):
        hp = os.path.join(frames_dir, f"c{i:02}.html"); pp = os.path.join(frames_dir, f"c{i:02}.png")
        open(hp, "w", encoding="utf-8").write(slide(c["kicker"], c["title"], c["visual"], brand))
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--screenshot={pp}",
                        "--window-size=1920,1080", "--force-device-scale-factor=1", f"file://{hp}"], capture_output=True)
        c["png"] = pp
        seg = os.path.join(segdir, f"s{i:02}.mp4"); c["seg"] = seg
        dur = c["dur"]; clip = c["visual"].get("clip")
        if clip and os.path.exists(clip):
            cd = probe_dur(clip) or dur
            # clip_hold: toca em velocidade natural e congela no último frame (terminal).
            # padrão: estica p/ preencher a cena (clipes de navegador sincronizados).
            pts = 1.0 if c["visual"].get("clip_hold") else (round(dur / cd, 4) if cd > 0 else 1.0)
            # preserva o aspecto do clipe (não distorce) e centraliza na moldura
            # (margens caem no fundo escuro da moldura = letterbox proposital)
            fc = (f"[1:v]scale={FW}:{FH}:force_original_aspect_ratio=decrease,"
                  f"setpts={pts}*PTS,fps=30,setsar=1[c];"
                  f"[0:v][c]overlay=x='{FX}+({FW}-w)/2':y='{FY}+({FH}-h)/2':eof_action=repeat[v]")
            cmd = ["ffmpeg","-y","-loop","1","-i",c["png"],"-i",clip,"-filter_complex",fc,
                   "-map","[v]","-t",str(dur),"-r","30","-c:v","libx264","-pix_fmt","yuv420p","-an",seg]
        else:
            cmd = ["ffmpeg","-y","-loop","1","-i",c["png"],"-t",str(dur),"-r","30",
                   "-vf","scale=1920:1080,format=yuv420p","-c:v","libx264","-pix_fmt","yuv420p","-an",seg]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  [ERRO] seg {i}:", r.stderr[-300:], flush=True)
    concat = os.path.join(frames_dir, "concat_seg.txt")
    with open(concat, "w") as f:
        for c in cues: f.write(f"file '{c['seg']}'\n")
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-i",audio,"-map","0:v:0","-map","1:a:0","-map_metadata","-1",
           "-c:v","libx264","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","160k",
           "-metadata:s:v:0","rotate=0","-t",str(round(audio_end+0.5,2)),out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("ffmpeg rc:", r.returncode, flush=True)
    print("VIDEO:", out, f"({os.path.getsize(out)/1e6:.1f} MB)" if r.returncode==0 else r.stderr[-500:], flush=True)
    return r.returncode == 0

def build_cues(C, SEGS, find_time):
    """C: [(anchor, kicker, title, visual)]. Retorna cues ordenadas com dur."""
    audio_end = max(s["end"] for s in SEGS if s["text"].strip())
    cues = []
    for anchor, kicker, title, visual in C:
        t = 0.0 if anchor is None else find_time(anchor)
        if t is None:
            print("  [AVISO] âncora não achada:", anchor, flush=True); continue
        cues.append({"start": t, "kicker": kicker, "title": title, "visual": visual})
    cues.sort(key=lambda c: c["start"])
    for i, c in enumerate(cues):
        c["end"] = cues[i+1]["start"] if i+1 < len(cues) else round(audio_end + 0.5, 2)
        c["dur"] = round(c["end"] - c["start"], 2)
    return cues
