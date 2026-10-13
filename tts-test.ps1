$token = (Get-Content 'C:\repo\voice-cloner\.env' | Where-Object { $_ -match '^TTS_API_TOKEN=' }).Split('=',2)[1]
$text = (Get-Content 'C:\repo\voice-cloner\aula-3-13-roteiro.md' -Raw).Substring(0, 1800)
$payload = @{ voice_id = 'diego'; language = 'Portuguese'; text = $text } | ConvertTo-Json -Compress
$headers = @{ Authorization = "Bearer $token" }
Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8787/v1/tts' -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -OutFile 'C:\repo\voice-cloner\output\aula-3-13-teste.mp3'
(Get-Item 'C:\repo\voice-cloner\output\aula-3-13-teste.mp3').Length
