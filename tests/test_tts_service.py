from pathlib import Path

import numpy as np
import soundfile as sf

from tts_service import TTSService, VoiceCatalog


def test_catalog_lists_supported_audio_and_rejects_traversal(tmp_path: Path):
    sf.write(tmp_path / "diego.wav", np.zeros(1000), 1000)
    (tmp_path / "ignored.txt").write_text("x")
    catalog = VoiceCatalog(tmp_path)
    assert catalog.list_voices()[0]["id"] == "diego"
    assert catalog.resolve_voice("diego").name == "diego.wav"
    try:
        catalog.resolve_voice("../secret")
    except ValueError:
        pass
    else:
        raise AssertionError("path traversal must be rejected")


def test_failed_model_load_exposes_recoverable_state(tmp_path: Path, monkeypatch):
    service = TTSService(tmp_path / "voices", tmp_path / "output", device="cpu")

    def fail_load():
        raise OSError("GPU unavailable")

    monkeypatch.setattr(service, "_load_model", fail_load)
    try:
        service.load_model()
    except RuntimeError as exc:
        assert str(exc) == "model loading failed"
    else:
        raise AssertionError("failed load must be reported")
    assert service.state == "failed"
    assert service.failure_reason == "OSError"


def test_generation_releases_queue_after_failure(tmp_path: Path, monkeypatch):
    service = TTSService(tmp_path / "voices", tmp_path / "output", model=object(), device="cpu")
    monkeypatch.setattr(service, "_generate_one", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    try:
        service.synthesize("diego", "Olá", "Portuguese")
    except RuntimeError:
        pass
    else:
        raise AssertionError("generation failure must propagate")
    assert service.state == "failed"
    assert service._condition.acquire(timeout=0.1)
    service._condition.release()
