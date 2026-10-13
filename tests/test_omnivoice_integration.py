from pathlib import Path
from unittest.mock import MagicMock
import numpy as np
import pytest
import soundfile as sf
import torch

from tts_service import TTSService, VoiceCatalog


def test_omnivoice_engine_initialization(tmp_path: Path):
    voices_dir = tmp_path / "voices"
    output_dir = tmp_path / "output"
    voices_dir.mkdir()

    service = TTSService(voices_dir, output_dir, device="cpu")
    assert service.engine == "omnivoice"
    assert service.model_id == "k2-fsa/OmniVoice"


def test_omnivoice_synthesize_mock_model(tmp_path: Path):
    voices_dir = tmp_path / "voices"
    output_dir = tmp_path / "output"
    voices_dir.mkdir()
    output_dir.mkdir()

    # Cria áudio de referência fake e transcrição
    ref_wav = voices_dir / "diego.wav"
    sf.write(ref_wav, np.zeros(24000), 24000)
    (voices_dir / "diego.txt").write_text("texto de referencia teste", encoding="utf-8")

    # Mock do modelo OmniVoice
    mock_model = MagicMock()
    mock_model.sampling_rate = 24000
    mock_model.generate.return_value = [torch.zeros((1, 24000))]

    service = TTSService(voices_dir, output_dir, model=mock_model, device="cpu")
    service.engine = "omnivoice"

    out = service.synthesize("diego", "Olá Garagem do Código!", "Portuguese")
    assert out.exists()
    assert out.suffix in [".mp3", ".wav"]
    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args.kwargs
    assert call_kwargs["text"] == "Olá Garagem do Código!"
    assert call_kwargs["language"] == "Portuguese"
    assert call_kwargs["ref_text"] == "texto de referencia teste"
