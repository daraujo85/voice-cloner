from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

SUPPORTED_LANGUAGES = ("Portuguese", "English", "Spanish")
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac"}
NATIVE_VOICE_PREFIX = "cv_"
VOICE_REF_TEXT = {
    "diego": os.getenv("REF_TEXT_DIEGO", ""),
    "heverton": os.getenv("REF_TEXT_HEVERTON", ""),
    "ivan": os.getenv("REF_TEXT_IVAN", ""),
}
LOG = logging.getLogger("tts")


def _ensure_omnivoice_path() -> None:
    for candidate in [
        os.getenv("VOICESTUDIO_PATH", ""),
        str(Path(__file__).resolve().parent.parent / "VoiceStudio"),
        "/mnt/c/repo/VoiceStudio",
        "C:/repo/VoiceStudio",
    ]:
        if candidate and os.path.isdir(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)
            break

import sys
_ensure_omnivoice_path()


class VoiceNotFoundError(ValueError):
    pass


def _is_native_voice(voice_id: str) -> bool:
    return voice_id.startswith(NATIVE_VOICE_PREFIX)


def _strip_native_prefix(voice_id: str) -> str:
    return voice_id[len(NATIVE_VOICE_PREFIX):] if _is_native_voice(voice_id) else voice_id


class TTSService:
    def __init__(
        self,
        voices_dir: Path,
        output_dir: Path,
        model: Any = None,
        device: str = "cuda",
        model_id: str | None = None,
        custom_model_id: str | None = None,
        enable_native: bool = True,
    ):
        self.catalog = VoiceCatalog(voices_dir)
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        self.engine = (os.getenv("TTS_ENGINE") or "omnivoice").lower()
        default_model = "k2-fsa/OmniVoice" if self.engine == "omnivoice" else "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        self.model_id = model_id or os.getenv("TTS_MODEL_ID", default_model)
        self.custom_model_id = custom_model_id or os.getenv(
            "TTS_CUSTOM_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
        )
        self.enable_native = enable_native

        self._clone_model = model
        self._custom_model = None
        self._native_speakers: list[str] = []
        self._native_speakers_meta: dict[str, dict] = {}

        self._state = "ready" if model is not None else "idle"
        self._failure_reason: str | None = None
        self._condition = threading.Condition()
        self._generation_timeout = float(os.getenv("TTS_GENERATION_TIMEOUT", "900"))
        self._queue_timeout = float(os.getenv("TTS_QUEUE_TIMEOUT", "1800"))

    @property
    def state(self) -> str:
        with self._condition:
            return self._state

    @property
    def ready(self) -> bool:
        return self.state in {"ready", "generating"}

    @property
    def failure_reason(self) -> str | None:
        with self._condition:
            return self._failure_reason

    def status(self) -> dict[str, Any]:
        with self._condition:
            return {"state": self._state, "reason": self._failure_reason}

    def _load_clone_model(self) -> None:
        import torch

        use_cuda = self.device.startswith("cuda") and torch.cuda.is_available()
        device = self.device if use_cuda else "cpu"

        if self.engine == "omnivoice":
            from omnivoice.models.omnivoice import OmniVoice
            from omnivoice.utils.dtype import tts_dtype_name

            dtype = getattr(torch, tts_dtype_name(device))
            model = OmniVoice.from_pretrained(
                self.model_id,
                device_map=device,
                dtype=dtype,
            )
            with self._condition:
                self._clone_model = model
                self.device = device
            return

        from qwen_tts import Qwen3TTSModel

        use_flash = device.startswith("cuda") and os.getenv("TTS_FLASH_ATTENTION", "false").lower() == "true"
        if use_flash:
            try:
                import flash_attn
            except ImportError:
                use_flash = False
        model = Qwen3TTSModel.from_pretrained(
            self.model_id,
            device_map=device,
            dtype=torch.float16 if device.startswith("cuda") else torch.float32,
            attn_implementation="flash_attention_2" if use_flash else "eager",
        )
        with self._condition:
            self._clone_model = model
            self.device = device

    def _load_custom_model(self) -> None:
        if self.engine == "omnivoice":
            with self._condition:
                self._custom_model = None
                self._native_speakers = []
            return

        import torch
        from qwen_tts import Qwen3TTSModel

        use_cuda = self.device.startswith("cuda") and torch.cuda.is_available()
        device = self.device if use_cuda else "cpu"
        use_flash = device.startswith("cuda") and os.getenv("TTS_FLASH_ATTENTION", "false").lower() == "true"
        if use_flash:
            try:
                import flash_attn
            except ImportError:
                use_flash = False
        model = Qwen3TTSModel.from_pretrained(
            self.custom_model_id,
            device_map=device,
            dtype=torch.float16 if device.startswith("cuda") else torch.float32,
            attn_implementation="flash_attention_2" if use_flash else "eager",
        )
        with self._condition:
            self._custom_model = model
            try:
                speakers = model.get_supported_speakers() or []
            except Exception:
                speakers = []
            self._native_speakers = [s for s in speakers if isinstance(s, str)]

    def load_model(self) -> None:
        with self._condition:
            if self._clone_model is not None:
                self._state = "ready"
                return
            if self._state == "loading":
                deadline = time.monotonic() + self._queue_timeout
                while self._state == "loading" and time.monotonic() < deadline:
                    self._condition.wait(timeout=max(0.1, deadline - time.monotonic()))
                if self._clone_model is not None:
                    return
                raise RuntimeError(self._failure_reason or "model loading timed out")
            self._state = "loading"
            self._failure_reason = None

        LOG.info("model_load_start model=%s device=%s", self.model_id, self.device)
        started = time.monotonic()
        custom_error: Exception | None = None
        try:
            self._load_model()
        except Exception as exc:
            with self._condition:
                self._state = "failed"
                self._failure_reason = type(exc).__name__
                self._condition.notify_all()
            LOG.exception("clone_model_load_failed elapsed_ms=%d", (time.monotonic() - started) * 1000)
            raise RuntimeError("model loading failed") from exc

        if self.enable_native:
            try:
                self._load_custom_model()
            except Exception as exc:
                custom_error = exc
                LOG.warning("custom_model_load_failed (fallback=disabled) err=%s", exc)
                self._custom_model = None
                self._native_speakers = []

        with self._condition:
            self._state = "ready"
            self._condition.notify_all()
        LOG.info(
            "model_load_done clone=%s custom=%s native_voices=%d elapsed_ms=%d",
            self.model_id,
            "ok" if self._custom_model is not None else "unavailable",
            len(self._native_speakers),
            (time.monotonic() - started) * 1000,
        )

    def _acquire_generation(self) -> None:
        deadline = time.monotonic() + self._queue_timeout
        with self._condition:
            while self._state == "generating":
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("generation queue timed out")
                self._condition.wait(timeout=remaining)
            if self._state == "failed":
                self._state = "idle"
            self._state = "generating"

    def _release_generation(self) -> None:
        with self._condition:
            self._state = "ready" if self._clone_model is not None else "failed"
            self._condition.notify_all()

    def _ensure_custom_loaded(self) -> None:
        if self._custom_model is not None:
            return
        if not self.enable_native:
            raise RuntimeError("native voices disabled")
        self._load_custom_model()

    def _generate_native(self, speaker: str, text: str, language: str, **params: Any) -> Path:
        self._ensure_custom_loaded()
        if speaker not in self._native_speakers:
            raise VoiceNotFoundError(f"native speaker not supported: {speaker}")
        kwargs: dict[str, Any] = {
            "text": text.strip(),
            "language": language,
            "speaker": speaker,
        }
        if params.get("temperature") is not None:
            kwargs["temperature"] = params["temperature"]
        if params.get("top_p") is not None:
            kwargs["top_p"] = params["top_p"]
        if params.get("top_k") is not None:
            kwargs["top_k"] = params["top_k"]
        if params.get("repetition_penalty") is not None:
            kwargs["repetition_penalty"] = params["repetition_penalty"]
        if params.get("max_new_tokens") is not None:
            kwargs["max_new_tokens"] = params["max_new_tokens"]
        wavs, sample_rate = self._custom_model.generate_custom_voice(**kwargs)
        waveform = wavs[0] if isinstance(wavs, list) or getattr(wavs, "ndim", 1) > 1 else wavs
        return self._write_audio(waveform, sample_rate)

    def _get_ref_text(self, voice_id: str) -> str:
        txt_path = self.catalog.voices_dir / f"{voice_id}.txt"
        if txt_path.is_file():
            return txt_path.read_text(encoding="utf-8").strip()
        env_val = os.getenv(f"REF_TEXT_{voice_id.upper()}")
        if env_val:
            return env_val
        return VOICE_REF_TEXT.get(voice_id, "")

    def _generate_clone(self, voice_id: str, text: str, language: str, **params: Any) -> Path:
        ref_audio = self.catalog.resolve_voice(voice_id)
        ref_text = self._get_ref_text(voice_id)

        if self.engine == "omnivoice":
            speed = float(params.get("speed", 1.0))
            audios = self._clone_model.generate(
                text=text.strip(),
                language=language,
                ref_audio=str(ref_audio),
                ref_text=ref_text or None,
                speed=speed,
                denoise=True,
                postprocess_output=True,
            )
            waveform = audios[0].cpu().float().squeeze().numpy()
            sample_rate = getattr(self._clone_model, "sampling_rate", 24000)
            return self._write_audio(waveform, sample_rate)

        kwargs = {
            "text": text.strip(),
            "language": language,
            "ref_audio": str(ref_audio),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.8),
            "repetition_penalty": params.get("repetition_penalty", 1.1),
        }
        if params.get("top_k") is not None:
            kwargs["top_k"] = params["top_k"]
        if params.get("max_new_tokens") is not None:
            kwargs["max_new_tokens"] = params["max_new_tokens"]
        kwargs.update(ref_text=ref_text or None, x_vector_only_mode=not bool(ref_text))
        wavs, sample_rate = self._clone_model.generate_voice_clone(**kwargs)
        waveform = wavs[0] if isinstance(wavs, list) or getattr(wavs, "ndim", 1) > 1 else wavs
        return self._write_audio(waveform, sample_rate)

    _load_model = _load_clone_model
    _generate_one = _generate_clone

    def _write_audio(self, waveform: Any, sample_rate: int) -> Path:
        wav_output = self.output_dir / f"{uuid.uuid4().hex}.wav"
        sf.write(wav_output, np.asarray(waveform), sample_rate)
        try:
            from pydub import AudioSegment
            mp3_output = wav_output.with_suffix(".mp3")
            AudioSegment.from_wav(wav_output).export(mp3_output, format="mp3", bitrate="320k")
            wav_output.unlink(missing_ok=True)
            return mp3_output
        except Exception:
            return wav_output

    def synthesize(self, voice_id: str, text: str, language: str, **params: Any) -> Path:
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        text = text.strip()
        if not text or len(text) > 2000:
            raise ValueError("text must contain 1 to 2000 characters")
        self.load_model()
        self._acquire_generation()
        started = time.monotonic()
        try:
            if _is_native_voice(voice_id):
                speaker = _strip_native_prefix(voice_id)
                result = self._generate_native(speaker, text, language, **params)
            else:
                result = self._generate_one(voice_id, text, language, **params)
            elapsed = time.monotonic() - started
            if elapsed > self._generation_timeout:
                with self._condition:
                    self._state = "failed"
                    self._failure_reason = "generation_timeout"
                raise RuntimeError("generation timed out")
            return result
        except Exception:
            with self._condition:
                self._failure_reason = "generation_failed"
                self._state = "failed"
            LOG.exception(
                "generation_failed voice=%s language=%s chars=%d elapsed_ms=%d",
                voice_id,
                language,
                len(text),
                (time.monotonic() - started) * 1000,
            )
            raise
        finally:
            if self.state != "failed":
                self._release_generation()
            else:
                with self._condition:
                    self._condition.notify_all()

    def synthesize_segments(self, voice_id: str, segments: list[dict[str, Any]], **params: Any) -> Path:
        if not segments or len(segments) > 32:
            raise ValueError("segments must contain 1 to 32 items")
        if sum(len(str(segment.get("text", ""))) for segment in segments) > 2000:
            raise ValueError("combined text must contain at most 2000 characters")
        outputs = []
        try:
            for segment in segments:
                outputs.append(self.synthesize(voice_id, segment["text"], segment["language"], **params))
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for output in outputs:
                combined += AudioSegment.from_file(output)
            result = self.output_dir / f"{uuid.uuid4().hex}-segments.mp3"
            combined.export(result, format="mp3", bitrate="320k")
            return result
        finally:
            for output in outputs:
                output.unlink(missing_ok=True)


class VoiceCatalog:
    def __init__(self, voices_dir: Path):
        self.voices_dir = voices_dir.resolve()

    def resolve_voice(self, voice_id: str) -> Path:
        if not voice_id or Path(voice_id).name != voice_id:
            raise VoiceNotFoundError("voice not found")
        matches = [p for p in self.voices_dir.glob(f"{voice_id}.*") if p.suffix.lower() in AUDIO_EXTENSIONS and p.is_file()]
        if not matches:
            raise VoiceNotFoundError("voice not found")
        return matches[0].resolve()

    def list_voices(self) -> list[dict[str, Any]]:
        result = []
        for path in sorted(self.voices_dir.iterdir() if self.voices_dir.exists() else []):
            if path.suffix.lower() not in AUDIO_EXTENSIONS or not path.is_file():
                continue
            try:
                info = sf.info(path)
                duration = round(info.frames / info.samplerate, 3)
            except Exception:
                duration = None
            result.append(
                {
                    "id": path.stem,
                    "name": path.stem,
                    "format": path.suffix.lower()[1:],
                    "duration": duration,
                    "type": "cloned",
                }
            )
        return result