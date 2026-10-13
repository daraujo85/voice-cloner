# AGENTS.md

## Telegram notifications

- Neste projeto, o Codex deve sempre enviar notificacoes de progresso via Telegram em tarefas substantivas sem depender de o usuario pedir novamente.
- Envie notificacoes em marcos relevantes: inicio do trabalho, progresso material, bloqueio concreto e conclusao.
- Use preferencialmente o script global `C:\Users\usuario\.codex\skills\telegram-progress-notifier\scripts\telegram_notify.py`.
- Resolva `BOT_TOKEN` e `CHAT_ID` nesta ordem:
  1. variaveis de ambiente da sessao atual
  2. arquivo `.env` da raiz deste projeto
  3. `C:\repo\pymacro\.env`
- Se a rede ou sandbox bloquear o envio, solicite aprovacao em vez de ignorar silenciosamente.
- Se as credenciais nao estiverem disponiveis, informe brevemente no chat e continue a tarefa.
## Encerramento do Codex no terminal

- Ao encerrar uma sessao interativa do Codex no terminal, envie `Ctrl+C` duas vezes.
- Aguarde a ultima mensagem de saida do Codex apos os dois `Ctrl+C`.
- Essa mensagem final costuma trazer resumo de execucao, incluindo uso de tokens e outros dados uteis.
- So considere a finalizacao concluida depois de receber essa ultima mensagem no terminal.
- Nao interrompa o processo antes dessa ultima saida, salvo se o usuario pedir explicitamente.

