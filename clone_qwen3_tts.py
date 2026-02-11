import argparse
import os
import sys
import torch
import soundfile as sf
import logging
import tempfile
from qwen_tts import Qwen3TTSModel
try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Clone voice using Qwen3-TTS-12Hz-1.7B-Base")
    parser.add_argument("--ref-audio", required=True, help="Path to reference audio file (WAV)")
    parser.add_argument("--ref-text", help="Transcript of the reference audio")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--language", default="Portuguese", help="Language of the output text (e.g., Portuguese, English, Chinese)")
    parser.add_argument("--out", default="output.wav", help="Output WAV file path")
    parser.add_argument("--x-vector-only", action="store_true", help="Use only speaker embedding (no reference text)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature (default: 0.7)")
    parser.add_argument("--top-p", type=float, default=0.8, help="Top-p sampling (default: 0.8)")
    parser.add_argument("--repetition-penalty", type=float, default=1.1, help="Repetition penalty (default: 1.1)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="Device to use (cuda or cpu)")
    parser.add_argument("--no-flash-attn", action="store_true", help="Disable Flash Attention 2 (use if you encounter errors)")

    args = parser.parse_args()

    # Validações
    if not os.path.exists(args.ref_audio):
        logger.error(f"Reference audio file not found: {args.ref_audio}")
        sys.exit(1)

    if not args.ref_text and not args.x_vector_only:
        logger.error("You must provide --ref-text UNLESS you use --x-vector-only.")
        sys.exit(1)

    # Pré-processamento de áudio de referência (suporte a OGG, MP3, etc.)
    ref_audio_path = args.ref_audio
    tmp_ref_wav = None
    
    if not args.ref_audio.lower().endswith(".wav"):
        if HAS_PYDUB:
            try:
                logger.info(f"Converting reference audio {args.ref_audio} to temporary WAV...")
                audio_ref = AudioSegment.from_file(args.ref_audio)
                tmp_ref = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_ref.close() # Fechar para permitir escrita/leitura
                
                audio_ref.export(tmp_ref.name, format="wav")
                ref_audio_path = tmp_ref.name
                tmp_ref_wav = tmp_ref.name
                logger.info(f"Converted to {ref_audio_path}")
            except Exception as e:
                logger.error(f"Failed to convert reference audio: {e}")
                # Tentar prosseguir com o arquivo original se falhar, talvez a lib interna suporte
        else:
            logger.warning("pydub not installed. If the model does not support this format natively, install pydub.")

    logger.info(f"Loading model Qwen/Qwen3-TTS-12Hz-1.7B-Base on {args.device}...")
    
    try:
        attn_impl = "flash_attention_2" if not args.no_flash_attn and args.device.startswith("cuda") else "eager"
        if args.no_flash_attn:
            logger.info("Flash Attention 2 disabled by user request.")
            
        model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map=args.device,
            dtype=torch.float16 if args.device.startswith("cuda") else torch.float32,
            attn_implementation=attn_impl,
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.info("Try running with --no-flash-attn if the error is related to Flash Attention.")
        sys.exit(1)

    logger.info("Model loaded successfully.")

    # Preparar argumentos para geração
    gen_kwargs = {
        "text": args.text,
        "language": args.language,
        "ref_audio": ref_audio_path,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "repetition_penalty": args.repetition_penalty,
    }

    if args.ref_text and not args.x_vector_only:
        gen_kwargs["ref_text"] = args.ref_text
    
    # Se x-vector-only for usado, precisamos passar um ref_text vazio ou controlar o modo
    if args.x_vector_only:
        # Tentar passar x_vector_only_mode=True se a API suportar
        gen_kwargs["x_vector_only_mode"] = True
        # Alguns métodos podem exigir ref_text mesmo que vazio ou ignorado
        # Mas verificamos que se x_vector_only_mode=True, ref_text pode ser None
        if "ref_text" not in gen_kwargs:
            gen_kwargs["ref_text"] = None

    logger.info(f"Ref audio info: {sf.info(ref_audio_path)}")
    logger.info(f"Synthesizing text: '{args.text}' in {args.language}...")
    logger.info("Starting generation (this might take a few seconds/minutes)...")
    
    try:
        # A API exata para clonagem no Base model pode ser generate ou generate_voice_clone
        # Baseado na pesquisa, generate_voice_clone parece ser o método
        if hasattr(model, "generate_voice_clone"):
            wavs, sr = model.generate_voice_clone(**gen_kwargs)
        elif hasattr(model, "generate"):
            # Fallback para generate se generate_voice_clone não existir
            wavs, sr = model.generate(**gen_kwargs)
        else:
            # Tentar inferir via custom_voice se for o caso, mas o modelo é Base
            logger.warning("Method generate_voice_clone not found. Trying generate_custom_voice as fallback (might fail for Base model).")
            wavs, sr = model.generate_custom_voice(**gen_kwargs)

        if isinstance(wavs, list) or (isinstance(wavs, torch.Tensor) and wavs.ndim > 1):
            wav_out = wavs[0]
        else:
            wav_out = wavs

        # Salvar áudio
        if args.out.lower().endswith(".mp3"):
            if not HAS_PYDUB:
                logger.warning("pydub not installed. Saving as WAV instead (install pydub for MP3 support).")
                args.out = args.out.rsplit(".", 1)[0] + ".wav"
                sf.write(args.out, wav_out, sr)
            else:
                # Salvar em arquivo temporário WAV e converter para MP3
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    tmp_wav_path = tmp_wav.name
                
                sf.write(tmp_wav_path, wav_out, sr)
                
                try:
                    audio = AudioSegment.from_wav(tmp_wav_path)
                    audio.export(args.out, format="mp3", bitrate="320k")
                    logger.info(f"Audio converted and saved to {args.out} (320k bitrate)")
                except Exception as e:
                    logger.error(f"Failed to export to MP3: {e}")
                    # Tentar salvar como WAV se falhar
                    backup_out = args.out.rsplit(".", 1)[0] + ".wav"
                    sf.write(backup_out, wav_out, sr)
                    logger.info(f"Saved as WAV instead: {backup_out}")
                finally:
                    if os.path.exists(tmp_wav_path):
                        os.remove(tmp_wav_path)
        else:
            sf.write(args.out, wav_out, sr)
            logger.info(f"Audio saved to {args.out}")

    except Exception as e:
        logger.error(f"Error during synthesis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Limpar arquivo temporário de referência se foi criado
        if tmp_ref_wav and os.path.exists(tmp_ref_wav):
            try:
                os.remove(tmp_ref_wav)
                logger.debug(f"Removed temporary reference file: {tmp_ref_wav}")
            except Exception as e:
                logger.warning(f"Could not remove temp file {tmp_ref_wav}: {e}")

if __name__ == "__main__":
    main()
