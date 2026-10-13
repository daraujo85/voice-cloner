# Aula 3.13 — Agentes econômicos

## Roteiro de narração

Até aqui, a gente falou sobre agentes capazes de usar ferramentas, tomar decisões e continuar um trabalho até chegar a uma resposta. Mas existe uma pergunta que aparece assim que colocamos esse agente para rodar de verdade: quanto software ele precisa produzir para resolver o problema?

Um agente pode ser competente e ainda assim ser caro, lento e exagerado. Pode criar arquivos demais, instalar dependências demais, explicar cada detalhe e transformar uma tarefa pequena em uma mudança difícil de revisar.

A frase-guia desta aula é simples: agente bom não é o que produz mais. É o que entrega o resultado necessário com o menor desperdício.

Para deixar essa ideia concreta, vamos comparar três formas de trabalhar. Primeiro, um agente sem instrução de economia. Depois, o Caveman: uma regra explícita para preferir a menor solução que funciona. Por fim, o Ponytail: um conjunto de práticas para reduzir código, contexto e complexidade sem remover validação, segurança ou acessibilidade.

A comparação precisa ser controlada. A mesma tarefa, o mesmo projeto inicial, o mesmo modelo e as mesmas ferramentas. Só mudamos a política de trabalho. Se mudarmos o projeto, o prompt e o conjunto de ferramentas ao mesmo tempo, não estaremos medindo economia. Estaremos misturando variáveis.

A tarefa escolhida é pequena de propósito. Vamos pedir uma melhoria localizada no projeto de laboratório: adicionar uma ferramenta simples ao harness, executar o fluxo existente e deixar um teste verificável. Não vamos reescrever o laboratório. Não vamos criar uma arquitetura nova. O objetivo é observar quanto cada agente altera para resolver exatamente esse pedido.

Antes de executar, definimos as métricas. Vamos registrar tempo total, número de chamadas ao modelo, tokens quando o provedor informar esse dado, arquivos alterados, linhas adicionadas e removidas, dependências novas, testes executados e resultado final.

Também existe uma métrica que não cabe em uma planilha: qualidade. A mudança funciona? O teste passa? O código é legível? O agente removeu alguma proteção? Uma solução menor que quebra comportamento não é econômica. É apenas incompleta.

Agora começa o primeiro experimento: o agente normal. Ele recebe a tarefa e trabalha com as instruções padrão. Observamos o caminho, sem interromper para corrigir estilo. Ao final, guardamos o diff e os números.

No segundo experimento, restauramos exatamente o mesmo estado inicial. O Caveman recebe a mesma tarefa, mas com uma política clara: não crie abstrações para um único caso, não adicione dependências sem necessidade, prefira a biblioteca padrão e pare quando o teste provar que o pedido foi atendido.

No terceiro experimento, restauramos o estado inicial novamente. O Ponytail recebe a mesma tarefa e acrescenta uma preocupação operacional: reduzir código e contexto, mas preservar fronteiras de confiança, tratamento de erros, testes e acessibilidade. A economia tem um limite. O que não pode ser simplificado continua existindo.

Depois dos três experimentos, não escolhemos um vencedor pelo menor número de linhas. Comparamos o resultado completo. Um agente pode escrever menos e gastar mais chamadas. Outro pode escrever mais, mas entregar uma solução mais fácil de manter. O ponto é tornar o trade-off visível.

Essa é a diferença entre otimizar produção e otimizar resultado. Produção é quantidade de texto, arquivos e código. Resultado é o comportamento correto, revisável e suficiente para o problema.

As políticas Caveman e Ponytail não são modelos mágicos. São limites de comportamento. Elas ajudam o agente a resistir à tentação de transformar qualquer pedido em um projeto inteiro. Mas continuam dependendo de contexto, revisão humana e testes.

Também não devemos transformar uma demonstração em uma lei universal. Os números mudam com o modelo, o prompt, o projeto, as ferramentas e a tarefa. O experimento mostra um método de comparação, não um ranking permanente.

A lição final é operacional. Cada linha que o agente produz passa a existir no nosso repositório. Cada dependência precisa ser atualizada. Cada arquivo precisa ser lido. Cada decisão extra aumenta superfície de revisão.

Por isso, a pergunta para o próximo agente não deveria ser apenas: você consegue fazer? Também deveria ser: qual é a menor mudança segura que prova que isso está feito?

Na próxima aula, vamos levar essa pergunta para um fluxo maior: como controlar escopo, contexto e validação quando o agente precisa executar várias etapas sem transformar autonomia em falta de controle.