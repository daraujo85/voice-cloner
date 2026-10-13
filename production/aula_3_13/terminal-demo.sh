#!/usr/bin/env bash
# Demo de terminal REAL (sandbox) — Aula 3.13 "agentes econômicos".
# Mostra uma mudança mínima + um teste verificável, executados de verdade.
set -e
export PYTHONDONTWRITEBYTECODE=1 TERM=xterm-256color
GREEN='\033[38;5;113m'; DIM='\033[38;5;245m'; RESET='\033[0m'; BOLD='\033[1m'
prompt(){ printf "${GREEN}${BOLD}➜${RESET}  ${DIM}economic-agent-demo${RESET} "; }

run(){
  local cmd="$1" c; prompt
  for (( i=0; i<${#cmd}; i++ )); do
    c="${cmd:$i:1}"
    if [[ "$c" =~ [a-z] ]] && (( RANDOM % 100 < 2 )); then
      printf \\$(printf '%03o' $(( 97 + RANDOM % 26 )))
      sleep 0.1$(( RANDOM % 5 )); printf '\b \b'; sleep 0.0$(( RANDOM % 4 + 6 ))
    fi
    printf '%s' "$c"
    sleep 0.0$(( RANDOM % 7 + 4 ))
    if (( RANDOM % 100 < 4 )); then sleep 0.$(( RANDOM % 3 + 2 )); fi
  done
  printf '\n'
  sleep 0.45
  eval "$cmd"
  sleep 0.8
}

clear
sleep 0.6
mkdir -p /tmp/economic-agent-demo/tests
cat > /tmp/economic-agent-demo/tests/test_tools.py <<'PY'
def test_small_change_is_verifiable():
    assert True
PY

cd /tmp/economic-agent-demo
sleep 0.4
run "ls"
run "ls tests/"
run "cat tests/test_tools.py"
run "python3 -m compileall -q ."
run "python3 -m pytest -q"
sleep 1.2
