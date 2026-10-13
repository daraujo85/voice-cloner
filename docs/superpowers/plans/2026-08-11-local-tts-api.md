# API local de TTS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expor o Qwen3-TTS por API HTTP Dockerizada, acessível somente na LAN, listar vozes/idiomas, gerar fala multilíngue com a melhor qualidade disponível e comparar com MiniMax.

**Architecture:** FastAPI carrega `Qwen3TTSModel` uma vez, resolve vozes dentro de `voices/`, valida token/idioma/texto e serializa gerações com lock. ICL mode (`ref_audio` + `ref_text`) será o padrão de qualidade; x-vector-only será fallback. Docker usa Python 3.11, `uv` e runtime NVIDIA. A skill `local-tts` faz healthcheck antes de qualquer chamada.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Pydantic, Qwen3-TTS, PyTorch CUDA, uv, Docker Compose, pytest.

## Global Constraints

- Rede local somente; sem Cloudflare ou internet pública.
- Python >=3.10 porque `accelerate==1.12.0` exige essa versão.
- Sem upload de referência nesta versão; `voice_id` só aponta para arquivo existente em `voices/`.
- Não registrar texto sintetizado, token ou segredos.
- Uma geração por vez para proteger VRAM.
- Healthcheck obrigatório na skill; PC desligado encerra sem fallback pago.
- Hardware documentado com dado real: NVIDIA RTX 3060, 12.288 MiB (12 GB), não 16 GB.
- Não apagar alterações existentes em `clone_qwen3_tts.py`, `.gitignore` ou `AGENTS.md`.
- Melhor qualidade: ICL com `ref_text`; x-vector-only somente quando não houver transcrição.
- Parâmetros configuráveis: `temperature`, `top_p`, `top_k`, `repetition_penalty`, `max_new_tokens`.
- Pigarro, risada e suspiro serão experimentos; tags explícitas não estão garantidas no Base.

## Fontes técnicas

- Qwen3-TTS README/model card: https://github.com/QwenLM/Qwen3-TTS
- `generate_voice_clone` suporta ICL com `ref_text` e x-vector-only; ICL é recomendado para melhor qualidade.
- O modelo lista Português, Inglês e Espanhol entre dez idiomas, e permite controle semântico de timbre, emoção e prosódia.

---

### Task 1: Corrigir metadados e dependências

**Files:** `pyproject.toml`, `uv.lock`

- [ ] Alterar `requires-python` para `>=3.10,<3.14` e adicionar `fastapi` e `uvicorn[standard]`.
- [ ] Rodar `uv lock`; esperar resolução sem erro.
- [ ] Rodar `uv sync`; esperar sucesso.
- [ ] Commitar: `git add pyproject.toml uv.lock && git commit -m "build: support Python runtime for TTS API"`.

### Task 2: Criar serviço testável de catálogo e síntese

**Files:** criar `tts_service.py`, `tests/test_tts_service.py`

- [ ] Testar que `VoiceCatalog.list_voices()` lista somente `.wav`, `.mp3`, `.ogg`, `.flac`, ordena IDs e rejeita `../secret`.
- [ ] Implementar `VoiceCatalog.list_voices() -> list[dict]` e `resolve_voice(voice_id: str) -> Path`, com duração via `soundfile` e proteção contra path traversal.
- [ ] Implementar `TTSService.synthesize(voice_id, text, language) -> Path`, limite de 2000 caracteres, lock, saída UUID `.mp3` e limpeza de temporários.
- [ ] Implementar ICL como padrão: referência com `ref_text` configurado por voz; passar `x_vector_only_mode=False`. Usar x-vector somente quando `ref_text` não existir.
- [ ] Passar parâmetros de qualidade ao modelo; usar CUDA/`float16` ou `bfloat16` compatível e Flash Attention 2 quando disponível.
- [ ] Testar com modelo falso que retorna waveform; rodar `uv run pytest tests/test_tts_service.py -q` e esperar PASS.
- [ ] Commitar: `git add tts_service.py tests/test_tts_service.py && git commit -m "feat: add serial local TTS service"`.

### Task 3: Implementar API HTTP autenticada

**Files:** criar `api.py`, `tests/test_api.py`

- [ ] Criar `TTSRequest` com `voice_id`, `text`, `language` e parâmetros de qualidade opcionais validados.
- [ ] Implementar `GET /health` público, retornando `status`, `device`, `model` e `ready`.
- [ ] Implementar `GET /v1/voices`, `GET /v1/languages` e `POST /v1/tts`; exigir `Authorization: Bearer` com `secrets.compare_digest` nos três.
- [ ] Retornar `404` para voz/idioma inexistente, `422` para entrada inválida, `409` quando lock estiver ocupado e MP3 com `audio/mpeg` no sucesso.
- [ ] Não carregar modelo real nos testes; injetar catálogo/serviço fake. Rodar `uv run pytest tests/test_api.py tests/test_tts_service.py -q` e esperar PASS.
- [ ] Commitar: `git add api.py tests/test_api.py && git commit -m "feat: expose authenticated local TTS API"`.

### Task 4: Dockerizar com CUDA e volumes

**Files:** criar `Dockerfile`, `docker-compose.yml`, `.dockerignore`; modificar `.env.example`, `README.md`

- [ ] Usar imagem CUDA compatível com PyTorch, Python 3.11 e `uv`; copiar lock antes do código e executar `uv sync --frozen`.
- [ ] Iniciar `uv run uvicorn api:app --host 0.0.0.0 --port 8787`.
- [ ] Compose deve publicar `8787:8787`, `gpus: all`, montar `voices` read-only e `output` gravável, definir `TTS_DEVICE=cuda`.
- [ ] Documentar token, LAN-only, firewall local, `docker compose build` e `docker compose up -d`.
- [ ] Rodar `docker compose config` e `docker compose build`; esperar sucesso.
- [ ] Commitar: `git add Dockerfile docker-compose.yml .dockerignore .env.example README.md && git commit -m "feat: dockerize local TTS API with NVIDIA runtime"`.

### Task 5: Smoke test real na RTX

**Artifact:** `output/smoke-api.mp3`, não commitar.

- [ ] Subir `docker compose up -d`; confirmar nos logs modelo carregado em CUDA.
- [ ] Consultar `/health`, `/v1/voices` e `/v1/languages` com token.
- [ ] Gerar com `voice_id=diego`, texto curto e `language=Portuguese`; validar com `ffprobe` duração, codec, sample rate e canais.
- [ ] Testar `English` e `Spanish` com a mesma voz somente depois do áudio português aprovado.
- [ ] Se áudio falhar, corrigir antes de gastar crédito MiniMax.

### Task 6: Criar skill `local-tts` com healthcheck

**Files:** criar `~/.claude/skills/local-tts/SKILL.md`, `local_tts.py`, `test_local_tts.py`

- [ ] Implementar comandos `health`, `voices`, `languages`, `generate --voice-id ID --language ID --text TEXT --output FILE`.
- [ ] Usar `LOCAL_TTS_URL`, `LOCAL_TTS_TOKEN`, `urllib.request` e timeout de 3 segundos.
- [ ] Todo comando, inclusive `voices`, `languages` e `generate`, chama `GET /health` primeiro; se falhar, retorna mensagem acionável com “Ligue o Duck Server” e não chama POST/MiniMax.
- [ ] Testar servidor indisponível, ordem health→POST, autenticação e gravação do MP3. Rodar `python3 test_local_tts.py` e esperar PASS.
- [ ] Instalar a pasta em `~/.claude/skills/local-tts/` sem token no arquivo.

### Task 7: Comparar Qwen3-TTS versus MiniMax

**Files:** criar `.pipeline/esa/tts-compare/README.md`, `textos.json`, `compare_manifest.json`, `generate_local.sh`, `generate_minimax.md`

- [ ] Usar exatamente a mesma fala, voz e intenção nos dois motores. Texto-base: `Esta voz foi gerada localmente pelo Qwen3-TTS. O modelo transforma texto em fala usando uma referência de voz e uma GPU NVIDIA RTX 3060 com doze gigabytes de memória. O processamento acontece na nossa própria máquina, sem enviar o áudio para um serviço externo.`
- [ ] Criar equivalentes em Português, Inglês e Espanhol, registrando hashes do texto, idioma e voz; nunca tokens.
- [ ] Gerar primeiro localmente via skill e validar inteligibilidade, duração e silêncio excessivo.
- [ ] Só então gerar pares MiniMax, uma chamada serial por idioma, registrando que consome créditos.
- [ ] Comparar latência, custo marginal, hardware, pronúncia, naturalidade, pausas, ruído e timbre; não declarar vencedor sem escuta humana.
- [ ] Testar separadamente frase com emoção e possíveis marcadores de pigarro/risada/suspiro. Reportar honestamente se forem tratados como texto literal.
- [ ] Criar visual lado a lado com players rotulados exatamente: `MiniMax Audio — consome créditos` e `Qwen3-TTS local — RTX 3060 12 GB`; sem emoji, usar SVG/componentes existentes.
- [ ] Commitar: `git add .pipeline/esa/tts-compare && git commit -m "docs: add local and hosted TTS comparison"`.

### Task 8: Inserir demonstração no plano da aula

**Files:** plano/roteiro da aula ESA correspondente; `.sessionflow/milestones.garagemdocodigo.json`

- [ ] Sequência: healthcheck, listar vozes, listar idiomas, gerar português, inglês e espanhol, ouvir pares, explicar Qwen3-TTS local/RTX 3060 12 GB versus créditos MiniMax.
- [ ] Texto explicativo: `O Qwen3-TTS é um modelo aberto de síntese e clonagem de voz que roda localmente. Usamos uma referência de voz, texto e uma RTX 3060 com 12 GB. A mesma mensagem pode ser sintetizada em Português, Inglês e Espanhol. O MiniMax é prático, mas cada geração consome créditos; no modelo local, depois da instalação, o custo marginal é a nossa máquina. A comparação usa a mesma fala para avaliar naturalidade, pronúncia, pausas e semelhança de timbre.`
- [ ] Manter demonstração prática; trocar visual a cada 12–15 segundos; comandos usados vão para Material, não `contentHtml`.
- [ ] Não publicar/substituir mídia até áudios, pares, VTT e playback serem validados. Preservar mídia anterior para rollback.
- [ ] Registrar hardware real, hashes, duração e resultado da escuta no marco.
