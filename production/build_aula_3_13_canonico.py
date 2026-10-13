#!/usr/bin/env python3
import json
import os
import sys

ROOT = "/Volumes/192.168.31.231/repo/voice-cloner"
sys.path.insert(0, os.path.join(ROOT, "production"))
import buildlib as B

SEGS = json.load(open(f"{ROOT}/output/aula-3-13-segs.json", encoding="utf-8"))["segments"]
AUDIO = f"{ROOT}/output/aula-3-13.mp3"
OUT = f"{ROOT}/output/aula-3-13-canonico.mp4"
FRAMES = f"{ROOT}/production/aula_3_13/frames"
CLIPS = f"{ROOT}/production/aula_3_13/clips"
BRAND = "Engenharia de Software na Era dos Agentes"
find_time = B.make_find_time(SEGS)

C = []
def add(anchor, kicker, title, visual):
    C.append((anchor, kicker, title, visual))

def clip(name, hold=False):
    return {"clip": os.path.join(CLIPS, name), "clip_hold": hold}

add(None, "agentes econômicos · aula 3.13", "Menos produção. Mais resultado.", {"graphic": B.g_statement("Agentes econômicos", "Como reduzir código, contexto e complexidade sem remover o que protege o produto.")})
add("Quanto sofrto é", "a pergunta", "Quanto precisa ser produzido?", {"graphic": B.g_statement("Competente não basta", "Um agente também pode ser caro, lento e exagerado.")})
add("Pode criar arquivos demais", "excesso", "Mais artefatos não significam mais valor", {"graphic": B.g_cards([("Arquivos", "Mais coisa para ler e revisar."), ("Dependências", "Mais superfície para atualizar.")])})
add("A frase guia desta aula", "a regra", "A menor solução que funciona", {"graphic": B.g_statement("Menos desperdício", "O objetivo é entregar o resultado necessário — não produzir o máximo de artefatos.")})
add("É o que entrega o resultado necessário", "resultado", "Produzir menos. Entregar o necessário.", {"graphic": B.g_beforeafter("Produção", "Quantidade de texto e arquivos", "Resultado", "Comportamento correto e suficiente")})
add("Para deixar essa ideia concreta", "três políticas", "A mesma tarefa, três formas de trabalhar", {"graphic": B.g_cards([("Normal", "Sem instrução explícita de economia."), ("Caveman", "A menor solução que funciona."), ("Ponytail", "Economia com segurança, testes e acessibilidade.")])})
add("Primeiro, um agente sem instrução de economia", "política 1", "Sem instrução de economia", {"graphic": B.g_statement("Agente normal", "Observamos o caminho sem corrigir estilo.")})
add("Depois o Cáveman", "política 2", "Caveman: menor solução que funciona", {"graphic": B.g_statement("Caveman", "Uma regra explícita para parar cedo.")})
add("Por fim, o Ponitel", "política 3", "Ponytail: economia com guardrails", {"graphic": B.g_statement("Ponytail", "Reduzir sem remover validação, segurança ou acessibilidade.")})
add("A comparação precisa ser controlada", "experimento", "Mudar uma variável por vez", {"graphic": B.g_steps(["Mesma tarefa", "Mesmo projeto", "Mesmo modelo", "Mesmas ferramentas", "Só muda a política"])})
add("Só mudamos a política de trabalho", "controle", "Política é a única variável", {"graphic": B.g_statement("Experimento controlado", "Se tudo muda ao mesmo tempo, não medimos economia.")})
add("Não estaremos medindo economia", "critério", "Misturar variáveis invalida a comparação", {"graphic": B.g_beforeafter("Medição", "Uma política muda", "Ruído", "Projeto, modelo e ferramentas mudam juntos")})
add("A tarefa escolhida é pequena", "escopo", "Uma melhoria localizada", {"graphic": B.g_beforeafter("Pedido", "Adicionar uma ferramenta simples e um teste verificável", "Limite", "Sem reescrever o laboratório nem criar arquitetura nova")})
add("Não vamos rejevê-lo laboratório", "limite", "Não reescrever o laboratório", {"graphic": B.g_statement("Escopo pequeno", "A tarefa existe para medir a política, não para criar um sistema novo.")})
add("Antes de executar", "métricas", "Medir produção e resultado", {"graphic": B.g_cards([("Tempo", "Duração e chamadas ao modelo."), ("Diff", "Arquivos e linhas alteradas."), ("Operação", "Dependências e testes."), ("Qualidade", "Comportamento correto e revisável.")])})
add("Arquivos alterados", "medição", "O diff também é um dado", {"graphic": B.g_steps(["Arquivos", "Linhas adicionadas", "Linhas removidas", "Dependências", "Testes"])})
add("A mudança funciona", "critério", "Menor não significa incompleta", {"graphic": B.g_beforeafter("Menor", "Poucas linhas, mas comportamento quebrado", "Econômica", "Mudança suficiente, protegida e verificável")})
add("Agora começa o primeiro experimento", "experimento 1", "Agente normal", clip("terminal.mp4", True))
add("No segundo experimento", "experimento 2", "Caveman: parar quando o teste provar", {"graphic": B.g_steps(["Não abstrair o único caso", "Não adicionar dependência", "Preferir biblioteca padrão", "Parar com teste verde"])})
add("No terceiro experimento", "experimento 3", "Ponytail: economia com limites", {"graphic": B.g_cards([("Reduzir", "Código, contexto e complexidade."), ("Preservar", "Fronteiras de confiança e erros."), ("Provar", "Testes, revisão e acessibilidade.")])})
add("Reduzir código e contexto", "guardrails", "Economia com limites", {"graphic": B.g_steps(["Reduzir código", "Reduzir contexto", "Preservar confiança", "Tratar erros", "Testar e revisar"])})
add("Depois dos três experimentos", "comparação", "Não escolher pelo menor diff", {"graphic": B.g_compare("Produção", ["Texto", "Arquivos", "Linhas"], "Resultado", ["Comportamento correto", "Revisável", "Suficiente"])})
add("Comparamos o resultado completo", "comparação", "O diff não conta história sozinho", {"graphic": B.g_statement("Resultado completo", "Menos linhas podem custar mais chamadas; mais linhas podem ser mais fáceis de manter.")})
add("Essa é a diferença", "trade-off", "Otimizar resultado, não volume", {"graphic": B.g_beforeafter("Otimizar produção", "Contar texto, arquivos e código", "Otimizar resultado", "Entregar comportamento correto e suficiente")})
add("As políticas Cáveman", "políticas", "Limites de comportamento, não modelos mágicos", {"graphic": B.g_statement("Caveman e Ponytail", "Ajudam a resistir à tentação de transformar qualquer pedido em um projeto inteiro.")})
add("Elas ajudam a resistir", "limite", "Não transformar tudo em projeto", {"graphic": B.g_cards([("Contexto", "Entender antes de agir."), ("Revisão", "Conferir o que mudou."), ("Teste", "Provar o comportamento.")])})
add("A lição final é operacional", "responsabilidade", "Cada linha entra no repositório", {"graphic": B.g_cards([("Dependência", "Precisa ser atualizada."), ("Arquivo", "Precisa ser lido."), ("Decisão", "Aumenta a superfície de revisão.")])})
add("Cada arquivo precisa ser lido", "revisão", "Toda mudança cria trabalho de revisão", {"graphic": B.g_statement("Superfície de revisão", "Cada arquivo e decisão extra precisa ser entendido.")})
add("Qual é a menor mudança segura", "pergunta", "Qual é a menor mudança segura que prova que está feito?", {"graphic": B.g_statement("Menor mudança segura", "Essa é a pergunta que acompanha o próximo agente.")})
add("Na próxima aula", "próximo passo", "Autonomia com controle", {"graphic": B.g_statement("Escopo, contexto e validação", "Várias etapas sem transformar autonomia em falta de controle.")})

add("A mesma tarefa, mas com uma política clara", "código mínimo", "A mudança pequena aparece no arquivo", clip("editor.mp4", True))
add("A economia tem um limite", "limites", "O que protege o produto continua existindo", {"graphic": B.g_statement("Simplificar não é remover proteção", "Validação, segurança, tratamento de erros, testes e acessibilidade continuam no escopo.")})
add("Também não devemos transformar", "método", "Experimento não é ranking permanente", {"graphic": B.g_steps(["Modelo", "Projeto", "Ferramentas", "Tarefa", "Contexto mudam"])})

cues = B.build_cues(C, SEGS, find_time)
assert len(cues) == len(C), f"cues perdidas: {len(C)-len(cues)}"
long_static = [c for c in cues if not c["visual"].get("clip") and c["dur"] > 15]
assert not long_static, [(c["kicker"], c["dur"]) for c in long_static]
print(f"cues: {len(cues)}/{len(C)} | dur alvo: {max(c['end'] for c in cues):.1f}s")
B.render_video(cues, AUDIO, OUT, BRAND, FRAMES)
