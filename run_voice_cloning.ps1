# Script para executar a clonagem usando o arquivo voice.wav

# Configurar encoding para UTF-8 para evitar problemas com caracteres especiais
$OutputEncoding = [System.Console]::InputEncoding = [System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Configuração de caminhos e nomes
$RefAudioPath = "c:\repo\voice-cloner\voices\heverton.wav"
$RefName = [System.IO.Path]::GetFileNameWithoutExtension($RefAudioPath)
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputDir = "c:\repo\voice-cloner\output"
$OutputFile = Join-Path -Path $OutputDir -ChildPath "${RefName}_${Timestamp}.mp3"

# Criar diretório de saída se não existir
if (-not (Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Diretório criado: $OutputDir"
}

# Opção 1: Clonagem Rápida (Sem transcrição do áudio original)
# Útil para testar rapidamente
Write-Host "Executando clonagem rápida (x-vector-only)..."
Write-Host "Arquivo de saída: $OutputFile"

python clone_qwen3_tts.py `
  --ref-audio $RefAudioPath `
  --x-vector-only `
  --text "Hoje acordei cedo e fui dar uma volta no bairro. O dia estava claro e o sol batia forte no asfalto. Um homem varria a rua enquanto um gato preto dormia no muro da casa ao lado. No mercado da esquina, uma fila longa se formava logo na porta.

Comprei queijo, leite e um pouco de mel. Voltei para casa com calma, ouvindo o som leve do vento nas folhas. No meio do caminho, vi um amigo de longa data e paramos para falar sobre trabalho, familia e planos para o futuro.

A vida tem um ritmo simples, mas real. Cada dia traz um novo desafio e uma nova meta. No final da tarde, sentei na sala, tomei cafe e pensei no valor de cada momento vivido." `
  --language Portuguese `
  --out $OutputFile `
  --temperature 0.7 `
  --top-p 0.8 `
  --repetition-penalty 1.1 `
  --no-flash-attn
