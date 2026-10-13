#!/usr/bin/env python3
"""CLI para clonagem de voz usando VoiceStudio (OmniVoice) no voice-cloner."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Resolver caminhos para import do OmniVoice
REPO_ROOT = Path(__file__).resolve().parent
for candidate in [
    os.getenv("VOICESTUDIO_PATH", ""),
    str(REPO_ROOT.parent / "VoiceStudio"),
    "/mnt/c/repo/VoiceStudio",
    "C:/repo/VoiceStudio",
]:
    if candidate and os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)
        break

import torch
import soundfile as sf
from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.dtype import tts_dtype_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("clone_omnivoice")


def main():
    parser = argparse.ArgumentParser(description="Clonagem de voz via OmniVoice (VoiceStudio)")
    parser.add_argument("--ref-audio", required=True, help="Caminho do áudio de referência (WAV, OGG, etc.)")
    parser.add_argument("--ref-text", help="Transcrição do áudio de referência")
    parser.add_argument("--text", required=True, help="Texto para sintetizar")
    parser.add_argument("--language", default="Portuguese", help="Idioma (Portuguese, English, Spanish, etc.)")
    parser.add_argument("--out", default="output/resultado.mp3", help="Arquivo de saída (.wav ou .mp3)")
    parser.add_argument("--speed", type=float, default=1.0, help="Velocidade da fala (default: 1.0)")
    parser.add_argument("--model", default="k2-fsa/OmniVoice", help="Modelo checkpoint HuggingFace")
    parser.add_argument("--device", default=None, help="Dispositivo (cuda ou cpu)")

    args = parser.parse_args()

    ref_audio = Path(args.ref_audio)
    if not ref_audio.exists():
        logger.error(f"Arquivo de referência não encontrado: {ref_audio}")
        sys.exit(1)

    ref_text = args.ref_text
    if not ref_text:
        txt_companion = ref_audio.with_suffix(".txt")
        if txt_companion.exists():
            ref_text = txt_companion.read_text(encoding="utf-8").strip()
            logger.info(f"Usando transcrição de {txt_companion}: {ref_text[:60]}...")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    dtype = getattr(torch, tts_dtype_name(device))

    logger.info(f"Carregando {args.model} em {device} ({dtype})...")
    model = OmniVoice.from_pretrained(args.model, device_map=device, dtype=dtype)

    logger.info(f"Sintetizando em {args.language}...")
    audios = model.generate(
        text=args.text.strip(),
        language=args.language,
        ref_audio=str(ref_audio),
        ref_text=ref_text or None,
        speed=args.speed,
        denoise=True,
        postprocess_output=True,
    )

    waveform = audios[0].cpu().float().squeeze().numpy()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.suffix.lower() == ".mp3":
        wav_tmp = out_path.with_suffix(".tmp.wav")
        sf.write(wav_tmp, waveform, model.sampling_rate)
        try:
            from pydub import AudioSegment
            AudioSegment.from_wav(wav_tmp).export(out_path, format="mp3", bitrate="320k")
            wav_tmp.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"pydub falhou na conversão para mp3 ({e}), mantendo WAV.")
            wav_tmp.rename(out_path.with_suffix(".wav"))
    else:
        sf.write(out_path, waveform, model.sampling_rate)

    duration = len(waveform) / model.sampling_rate
    logger.info(f"Áudio gerado com sucesso: {out_path} ({duration:.2f}s)")


if __name__ == "__main__":
    main()
