from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
FRAMES = OUT / "aula-3-13-frames"
AUDIO = OUT / "aula-3-13.mp3"
SEGS = OUT / "aula-3-13-segs.json"
VIDEO = OUT / "aula-3-13.mp4"

BG = (17, 24, 39)
PANEL = (31, 41, 55)
WHITE = (243, 244, 246)
MUTED = (156, 163, 175)
ACCENT = (96, 165, 250)


def font(size: int, bold: bool = False):
    name = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    return ImageFont.truetype(name, size)


def fit(text: str, fnt, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if fnt.getlength(candidate) <= width:
            line = candidate
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    return lines


def make_frame(index: int, text: str):
    image = Image.new("RGB", (1920, 1080), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((120, 116, 1800, 964), fill=PANEL)
    draw.rectangle((120, 116, 132, 964), fill=ACCENT)
    label = "AGENTES ECONÔMICOS  /  AULA 3.13"
    draw.text((180, 170), label, font=font(28, True), fill=ACCENT)
    title = "Menos produção. Mais resultado." if index == 0 else ("A menor mudança segura" if index >= 65 else "Economia com qualidade")
    draw.text((180, 250), title, font=font(58, True), fill=WHITE)
    body_font = font(42)
    y = 390
    for line in fit(text, body_font, 1420)[:6]:
        draw.text((180, y), line, font=body_font, fill=WHITE)
        y += 64
    draw.text((180, 875), f"{index + 1:02d}", font=font(32, True), fill=MUTED)
    image.save(FRAMES / f"{index:04d}.png")


def main():
    data = json.loads(SEGS.read_text())
    segments = data["segments"]
    FRAMES.mkdir(parents=True, exist_ok=True)
    for i, segment in enumerate(segments):
        make_frame(i, segment["text"].strip())
    concat = OUT / "aula-3-13-video.txt"
    lines = []
    for i, segment in enumerate(segments):
        duration = max(0.1, segment["end"] - segment["start"])
        lines += [f"file '{(FRAMES / f'{i:04d}.png').as_posix()}'", f"duration {duration:.3f}"]
    lines.append(f"file '{(FRAMES / f'{len(segments)-1:04d}.png').as_posix()}'")
    concat.write_text("\n".join(lines))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(AUDIO), "-map", "0:v", "-map", "1:a", "-t", str(data.get("duration", segments[-1]["end"])), "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(VIDEO)], check=True)
    print(VIDEO)


if __name__ == "__main__":
    main()
