from __future__ import annotations

import hmac
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from tts_service import (
    NATIVE_VOICE_PREFIX,
    SUPPORTED_LANGUAGES,
    TTSService,
    VoiceNotFoundError,
    _is_native_voice,
    _strip_native_prefix,
)

BASE_DIR = Path(__file__).resolve().parent
TOKEN = os.getenv("TTS_API_TOKEN", "")
ENABLE_NATIVE = os.getenv("TTS_ENABLE_NATIVE", "true").lower() == "true"
SERVICE = TTSService(
    voices_dir=Path(os.getenv("TTS_VOICES_DIR", BASE_DIR / "voices")),
    output_dir=Path(os.getenv("TTS_OUTPUT_DIR", BASE_DIR / "output")),
    device=os.getenv("TTS_DEVICE", "cuda"),
    enable_native=ENABLE_NATIVE,
)
LOG = logging.getLogger("tts.api")
app = FastAPI(title="Local TTS API", version="1.1.0")


class SegmentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: str

    @field_validator("language")
    @classmethod
    def supported_language(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError(f"language must be one of: {', '.join(SUPPORTED_LANGUAGES)}")
        return value


class SegmentsRequest(BaseModel):
    voice_id: str = Field(min_length=1, max_length=100)
    segments: list[SegmentRequest] = Field(min_length=1, max_length=32)
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.8, gt=0, le=1)
    repetition_penalty: float = Field(default=1.1, ge=0.5, le=2)


class TTSRequest(BaseModel):
    voice_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=2000)
    language: str
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.8, gt=0, le=1)
    top_k: int | None = Field(default=None, ge=1, le=500)
    repetition_penalty: float = Field(default=1.1, ge=0.5, le=2)
    max_new_tokens: int | None = Field(default=None, ge=1, le=10000)

    @field_validator("language")
    @classmethod
    def supported_language(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError(f"language must be one of: {', '.join(SUPPORTED_LANGUAGES)}")
        return value


async def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
    if not TOKEN or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if not hmac.compare_digest(authorization[7:], TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")


def _service_status() -> dict:
    return SERVICE.status() if hasattr(SERVICE, "status") else {"state": "ready" if SERVICE.ready else "loading", "reason": None}


@app.on_event("startup")
def preload_model() -> None:
    if os.getenv("TTS_PRELOAD", "true").lower() != "true":
        return
    threading.Thread(target=SERVICE.load_model, name="tts-model-loader", daemon=True).start()


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        LOG.exception("request_failed request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
        raise
    response.headers["X-Request-ID"] = request_id
    LOG.info("request_done request_id=%s method=%s path=%s status=%d elapsed_ms=%d", request_id, request.method, request.url.path, response.status_code, (time.monotonic() - started) * 1000)
    return response


@app.get("/health")
def health() -> dict:
    state = _service_status()
    body = {
        "status": "ok" if state["state"] in {"ready", "generating"} else "unavailable",
        "ready": state["state"] in {"ready", "generating"},
        "state": state["state"],
        "reason": state["reason"],
        "device": SERVICE.device,
        "model": SERVICE.model_id,
        "custom_model": SERVICE.custom_model_id if SERVICE.enable_native else None,
        "native_voices_loaded": bool(SERVICE._native_speakers),
    }
    if body["status"] != "ok":
        return Response(status_code=503, media_type="application/json", content=__import__("json").dumps(body))
    return body


def _native_voices_payload() -> list[dict]:
    return [
        {
            "id": f"{NATIVE_VOICE_PREFIX}{speaker}",
            "name": speaker,
            "type": "native",
            "format": "synthesized",
            "duration": None,
            "native_lang": meta.get("native_lang"),
            "description": meta.get("description"),
        }
        for speaker, meta in SERVICE._native_speakers_meta.items()
    ]


def _merge_voices() -> list[dict]:
    cloned = SERVICE.catalog.list_voices()
    natives = _native_voices_payload()
    cloned_ids = {v["id"] for v in cloned}
    for native in natives:
        native_id = native["id"]
        if native_id in cloned_ids:
            LOG.warning("voice_id_collision id=%s (cloned wins)", native_id)
    return cloned + [n for n in natives if n["id"] not in cloned_ids]


@app.get("/v1/voices", dependencies=[Depends(require_token)])
def voices() -> dict:
    return {"voices": _merge_voices()}


@app.get("/v1/languages", dependencies=[Depends(require_token)])
def languages() -> dict:
    return {"languages": [{"id": item, "name": item} for item in SUPPORTED_LANGUAGES]}


def _validate_voice_id(voice_id: str) -> None:
    if _is_native_voice(voice_id):
        speaker = _strip_native_prefix(voice_id)
        if not SERVICE._native_speakers or speaker not in SERVICE._native_speakers:
            raise VoiceNotFoundError(f"native voice not available: {voice_id}")
    else:
        SERVICE.catalog.resolve_voice(voice_id)


def _synthesis_error(exc: RuntimeError) -> HTTPException:
    message = str(exc)
    if "timed out" in message:
        return HTTPException(status_code=504, detail="synthesis timed out; service is recovering")
    if "loading" in message:
        return HTTPException(status_code=503, detail="model is loading or unavailable")
    return HTTPException(status_code=500, detail="synthesis failed")


@app.post("/v1/tts/segments", dependencies=[Depends(require_token)])
def tts_segments(payload: SegmentsRequest) -> Response:
    try:
        _validate_voice_id(payload.voice_id)
        path = SERVICE.synthesize_segments(
            payload.voice_id,
            [segment.model_dump() for segment in payload.segments],
            temperature=payload.temperature,
            top_p=payload.top_p,
            repetition_penalty=payload.repetition_penalty,
        )
    except VoiceNotFoundError:
        raise HTTPException(status_code=404, detail="voice not found")
    except RuntimeError as exc:
        raise _synthesis_error(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return Response(path.read_bytes(), media_type="audio/mpeg", headers={"X-Audio-Path": path.name})


@app.post("/v1/tts", dependencies=[Depends(require_token)])
def tts(payload: TTSRequest) -> Response:
    try:
        _validate_voice_id(payload.voice_id)
        path = SERVICE.synthesize(
            payload.voice_id,
            payload.text,
            payload.language,
            temperature=payload.temperature,
            top_p=payload.top_p,
            top_k=payload.top_k,
            repetition_penalty=payload.repetition_penalty,
            max_new_tokens=payload.max_new_tokens,
        )
    except VoiceNotFoundError:
        raise HTTPException(status_code=404, detail="voice not found")
    except RuntimeError as exc:
        raise _synthesis_error(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return Response(path.read_bytes(), media_type="audio/mpeg" if path.suffix == ".mp3" else "audio/wav", headers={"X-Audio-Path": path.name})