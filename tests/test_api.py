from pathlib import Path

from fastapi.testclient import TestClient

import api


class FakeCatalog:
    def list_voices(self):
        return [{"id": "diego", "format": "wav"}]

    def resolve_voice(self, voice_id: str):
        return Path("/tmp/fake-voice.wav")


class FakeService:
    ready = True
    device = "cpu"
    model_id = "fake"
    custom_model_id = None
    enable_native = False
    _native_speakers = []
    _native_speakers_meta = {}
    catalog = FakeCatalog()

    def synthesize(self, *args, **kwargs):
        path = Path("/tmp/fake-tts.wav")
        path.write_bytes(b"RIFFfake")
        return path

    def synthesize_segments(self, *args, **kwargs):
        path = Path("/tmp/fake-segments.mp3")
        path.write_bytes(b"ID3fake")
        return path


def test_health_is_public(monkeypatch):
    monkeypatch.setattr(api, "SERVICE", FakeService())
    assert TestClient(api.app).get("/health").status_code == 200


def test_protected_endpoint_requires_bearer(monkeypatch):
    monkeypatch.setattr(api, "TOKEN", "secret")
    client = TestClient(api.app)
    assert client.get("/v1/voices").status_code == 401
    assert client.get("/v1/voices", headers={"Authorization": "Bearer secret"}).status_code == 200


def test_tts_returns_audio(monkeypatch):
    monkeypatch.setattr(api, "TOKEN", "secret")
    monkeypatch.setattr(api, "SERVICE", FakeService())
    response = TestClient(api.app).post(
        "/v1/tts",
        headers={"Authorization": "Bearer secret"},
        json={"voice_id": "diego", "text": "Olá", "language": "Portuguese"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"


def test_segmented_tts_returns_audio(monkeypatch):
    monkeypatch.setattr(api, "TOKEN", "secret")
    monkeypatch.setattr(api, "SERVICE", FakeService())
    response = TestClient(api.app).post(
        "/v1/tts/segments",
        headers={"Authorization": "Bearer secret"},
        json={"voice_id": "diego", "segments": [
            {"text": "Olá", "language": "Portuguese"},
            {"text": "welcome back", "language": "English"},
        ]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
