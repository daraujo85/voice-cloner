# Script para executar a clonagem em Espanhol com o hino do Real Madrid

# Configurar encoding para UTF-8
$OutputEncoding = [System.Console]::InputEncoding = [System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Configuração de caminhos e nomes
$RefAudioPath = "c:\repo\voice-cloner\voices\ivan.ogg"
$RefName = [System.IO.Path]::GetFileNameWithoutExtension($RefAudioPath)
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputDir = "c:\repo\voice-cloner\output"
$OutputFile = Join-Path -Path $OutputDir -ChildPath "${RefName}_${Timestamp}.mp3"

# Criar diretório de saída se não existir
if (-not (Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Diretório criado: $OutputDir"
}

Write-Host "Executando clonagem em Espanhol (Hino do Real Madrid)..."
Write-Host "Arquivo de saída: $OutputFile"

# Nota: O texto contém o refrão do hino "Hala Madrid y nada más"
python clone_qwen3_tts.py `
  --ref-audio $RefAudioPath `
  --x-vector-only `
  --text "Historia que tú hiciste, historia por hacer, porque nadie resiste tus ganas de vencer. Ya salen las estrellas, mi viejo Chamartín, de lejos y de cerca nos traes hasta aquí. Llevo tu camiseta pegada al corazón, los días que tú juegas son todo lo que soy. ¡Hala Madrid y nada más! ¡Y nada más! ¡Hala Madrid!" `
  --language Spanish `
  --out $OutputFile `
  --temperature 0.7 `
  --top-p 0.8 `
  --repetition-penalty 1.1 `
  --no-flash-attn
