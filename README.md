# Voice Cloner (Qwen3-TTS)

Este projeto permite clonar vozes usando o modelo `Qwen3-TTS-12Hz-1.7B-Base`, com suporte para exportação em MP3 e uso de diversos formatos de áudio como referência.

## Estrutura do Projeto

- `voices/`: Pasta para armazenar os áudios de referência (ignorada pelo Git).
- `output/`: Pasta onde os áudios clonados são salvos (ignorada pelo Git).
- `pyproject.toml`: Arquivo de configuração de dependências do projeto (UV).
- `.env`: Arquivo de configuração de caminhos (não comitado).
- `.env.example`: Exemplo de configuração de ambiente.
- `.gitignore`: Arquivo de exclusão do Git.
- `clone_qwen3_tts.py`: Script principal Python.
- `run_voice_cloning.ps1`: Script PowerShell para clonagem em Português.
- `run_voice_cloning_es.ps1`: Script PowerShell para clonagem em Espanhol.

## Pré-requisitos

- **Python 3.10+**
- **UV** (Gerenciador de projetos Python moderno e rápido).
- **FFmpeg**: Necessário para suporte a MP3 e conversão de formatos de áudio.
- **GPU NVIDIA** (Recomendado): Com drivers CUDA instalados para melhor performance.

## Instalação

1. Clone o repositório e entre na pasta:

   ```bash
   git clone <url-do-repositorio>
   cd voice-cloner
   ```

2. Instale as dependências com UV:

   ```bash
   uv sync
   ```

3. Em ambiente NVIDIA, instale PyTorch com CUDA compatível quando necessário:

   ```bash
   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

4. Configure `.env` a partir de `.env.example`.

## Uso

### Scripts de Automação

```powershell
.\run_voice_cloning.ps1
.\run_voice_cloning_es.ps1
```

Os resultados são salvos em `output/` em formato MP3.

### Uso Manual

```bash
uv run clone_qwen3_tts.py \
  --ref-audio "voices/sua_voz.ogg" \
  --ref-text "Transcrição exata da referência" \
  --text "Texto para falar" \
  --language Portuguese \
  --out "output/resultado.mp3" \
  --temperature 0.7
```

Parâmetros principais: `--ref-audio`, `--ref-text`, `--text`, `--language`, `--out`, `--x-vector-only`, `--temperature`, `--top-p` e `--repetition-penalty`.

## API local FastAPI

A API expõe o modelo somente na LAN, com token Bearer nos endpoints protegidos. No Duck Server:

```bash
docker compose build
docker compose up -d
curl http://localhost:8787/health
curl -H "Authorization: Bearer $TTS_API_TOKEN" http://localhost:8787/v1/voices
```

Endpoints: `GET /health`, `GET /v1/voices`, `GET /v1/languages`, `POST /v1/tts` e `POST /v1/tts/segments`. A geração é serializada para proteger a VRAM.

Para texto misto, teste primeiro uma chamada única. Se a troca de idioma soar estranha, envie segmentos explícitos; a API gera cada trecho no idioma correto e concatena os áudios:

```json
{
  "voice_id": "diego",
  "segments": [
    {"text": "Esta é uma frase em português.", "language": "Portuguese"},
    {"text": "This part is generated in English.", "language": "English"}
  ]
}
```

Use `POST /v1/tts/segments` para o teste controlado. A junção acontece localmente, sem MiniMax. A skill `local-tts` verifica `/health` antes de listar ou gerar e não usa fallback MiniMax.

ICL é usado quando `REF_TEXT_<VOICE_ID>` contém a transcrição da referência. Sem transcrição, o serviço usa x-vector-only. Idiomas iniciais: `Portuguese`, `English`, `Spanish`.

A máquina validada tem NVIDIA RTX 3060 com 12 GB de VRAM. Não publique essa API via Cloudflare; restrinja a porta 8787 à LAN.

## Desenvolvimento

```bash
uv sync
uv run pytest tests -q
```

Os testes sem GPU cobrem API, autenticação, catálogo e path traversal. Smoke test de síntese deve rodar no Duck Server com Docker e CUDA.

Pigarro, risada e suspiro são experimentos: o modelo Base pode interpretar marcadores como texto literal. Gere áudio local primeiro; compare com MiniMax somente após validar inteligibilidade e timbre. Vídeos publicados precisam de VTT e rollback da mídia anterior.
