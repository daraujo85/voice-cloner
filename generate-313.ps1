$ErrorActionPreference = 'Stop'
$token = (Get-Content 'C:\repo\voice-cloner\.env' | Where-Object { $_ -match '^TTS_API_TOKEN=' }).Split('=',2)[1]
$text = Get-Content 'C:\repo\voice-cloner\aula-3-13-roteiro.md' -Raw
$sentences = [regex]::Split($text, '(?<=[.!?])\s+') | Where-Object { $_.Trim().Length -gt 0 }
$chunks = @(); $current = ''
foreach ($sentence in $sentences) { if (($current.Length + $sentence.Length + 1) -gt 1800) { $chunks += $current.Trim(); $current = '' }; $current += ' ' + $sentence }
if ($current.Trim()) { $chunks += $current.Trim() }
$headers = @{ Authorization = "Bearer $token" }; $paths = @()
for ($i = 0; $i -lt $chunks.Count; $i++) {
  $payload = @{ voice_id = 'diego'; language = 'Portuguese'; text = $chunks[$i] } | ConvertTo-Json -Compress
  $path = "C:\repo\voice-cloner\output\aula-3-13-$i.mp3"
  Write-Output "Gerando chunk $i/$($chunks.Count) ($($chunks[$i].Length) chars)"
  Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8787/v1/tts' -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -OutFile $path
  $paths += $path
}
$list = @(); foreach ($p in $paths) { $list += "file '$p'" }; $list | Set-Content -Encoding ascii 'C:\repo\voice-cloner\output\aula-3-13.txt'
ffmpeg -y -f concat -safe 0 -i 'C:\repo\voice-cloner\output\aula-3-13.txt' -c:a libmp3lame -b:a 192k 'C:\repo\voice-cloner\output\aula-3-13.mp3' 2>&1 | Select-Object -Last 3
Get-Item 'C:\repo\voice-cloner\output\aula-3-13.mp3' | Select-Object Length,LastWriteTime
