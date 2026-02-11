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

- **Python 3.9+**
- **UV** (Gerenciador de projetos Python moderno e rápido).
- **FFmpeg**: Necessário para suporte a MP3 e conversão de formatos de áudio.
  - No Windows: `winget install ffmpeg` ou baixe do site oficial e adicione ao PATH.
- **GPU NVIDIA** (Recomendado): Com drivers CUDA instalados para melhor performance.

## Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd voice-cloner
    ```

2.  **Crie o ambiente e instale as dependências com UV:**
    O projeto já está configurado com `pyproject.toml`.

    ```bash
    # Cria o venv e instala as dependências básicas
    uv sync
    ```

3.  **Instale PyTorch com suporte a CUDA (Importante):**
    O `uv` pode instalar a versão correta do PyTorch. Ajuste conforme sua versão do CUDA (ex: cu121 para CUDA 12.1):

    ```bash
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    ```

4.  **Configure o arquivo `.env`:**
    Copie o arquivo de exemplo e ajuste os caminhos se necessário.
    ```bash
    cp .env.example .env
    ```
    Conteúdo padrão do `.env`:
    ```ini
    REF_AUDIO_PT=voices/heverton.wav
    REF_AUDIO_ES=voices/ivan.ogg
    OUTPUT_DIR=output
    ```

## Uso

### Scripts de Automação (Recomendado)

Use os scripts PowerShell para facilitar a execução. Eles configuram automaticamente o encoding, caminhos e geram nomes de arquivos com data/hora.

1.  **Português (Texto de Livro):**
    Edite o script para apontar para seu áudio de referência em `voices/`.
    ```powershell
    .\run_voice_cloning.ps1
    ```

2.  **Espanhol (Hino do Real Madrid):**
    ```powershell
    .\run_voice_cloning_es.ps1
    ```

Os resultados serão salvos na pasta `output/` em formato MP3 (320kbps).

### Uso Manual (Python)

Você pode chamar o script Python diretamente via `uv run`:

```bash
uv run clone_qwen3_tts.py ^
  --ref-audio "voices/sua_voz.ogg" ^
  --text "Texto para falar" ^
  --language Portuguese ^
  --out "output/resultado.mp3" ^
  --temperature 0.7
```

**Parâmetros Principais:**
- `--ref-audio`: Caminho para o áudio de voz (WAV, MP3, OGG, etc.).
- `--text`: Texto a ser falado.
- `--language`: Idioma (Portuguese, Spanish, English, etc.).
- `--out`: Arquivo de saída (use .mp3 para MP3).
- `--x-vector-only`: Usa apenas o timbre da voz (ignora o conteúdo do áudio de referência).
- `--temperature`, `--top-p`: Ajustes de criatividade e qualidade da voz.

## Notas

- **Formatos de Áudio**: O sistema aceita automaticamente OGG, MP3 e outros formatos como referência, convertendo temporariamente para WAV.
- **Acentos**: Para melhores resultados, prefira textos sem acentos se notar falhas na pronúncia.
