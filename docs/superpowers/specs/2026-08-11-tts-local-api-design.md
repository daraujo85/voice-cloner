# API local para clonagem de voz

## Objetivo
Expor o `Qwen3-TTS-12Hz-1.7B-Base` por HTTP somente na rede local, usando a GPU NVIDIA do Duck Server, sem créditos do MiniMax.

## API
- `GET /health`: status, dispositivo e modelo carregado.
- `GET /v1/voices`: lista arquivos de áudio existentes em `voices/`, com `id`, nome, formato e duração.
- `GET /v1/languages`: lista IDs e nomes dos idiomas suportados pelo modelo.
- `POST /v1/tts`: recebe `voice_id`, `text` e `language`; retorna MP3 (`audio/mpeg`).
- Todos os endpoints, exceto health, exigem `Authorization: Bearer` igual ao token configurado por ambiente.

## Segurança e limites
- Sem upload de referência na primeira versão.
- `voice_id` resolve somente arquivos dentro de `voices/`; rejeitar path traversal.
- Texto não vazio, com limite configurado.
- Idioma validado contra catálogo suportado.
- Mutex global permite uma geração por vez para proteger VRAM.
- Não registrar texto ou token em logs.

## Execução
- Docker com Python compatível com `qwen-tts` e `uv`.
- GPU NVIDIA via runtime NVIDIA.
- `voices/` e `output/` como volumes.
- Bind HTTP em `0.0.0.0`, publicado para a LAN; sem Cloudflare.

## Verificação
- Testes de health, autenticação, listagem, validação de voz/idioma/texto e geração.
- Smoke test real na RTX com download do MP3 e inspeção de duração/formato.
