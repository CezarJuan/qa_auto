# Design

## Context

O explore (docs/) mapeou o estado atual: interface Streamlit, API FastAPI com `/gerar` e `/saude`, retry com erro devolvido ao LLM e validação estrutural funcionando, 12 testes passando, todos no backend. O fluxo real com `llama3.1:8b` teve 3 timeouts de 90 s em 6 execuções, todos nas primeiras chamadas, o que sugere carga inicial do modelo (hipótese, não confirmada).

## Goals / Non-Goals

**Goals:**
- Fluxo real reproduzível de ponta a ponta para os 5 exemplos, sem exceções na interface.
- Cobertura de testes também na interface, nos pontos onde ficaram os bugs.

**Non-Goals:**
- Melhorar a qualidade semântica do modelo extraído (changes 2 e 3).
- Gerar testes reais (change 4). Aqui só escondemos os artefatos falsos.

## Decisions

1. **Identificador do nó ≠ rótulo.** O diagrama usa um id ASCII derivado do nome (sem acento, PascalCase, só `[A-Za-z0-9_]`) e declara o nome original como rótulo (`state "Com itens" as ComItens`). Alternativa: exigir PascalCase no LLM. Foi descartada porque o LLM real gerou "Com itens" e o diagrama não deve depender disso. O formato do id no modelo fica para `fsm-model-v2`.
2. **Uma configuração de tempo, lida pelos dois lados.** `TEMPO_LIMITE_CHAMADA` e `ORCAMENTO_TOTAL_GERACAO` ficam no `.env`. O backend para de tentar quando a próxima tentativa não cabe no orçamento. O front usa `ORCAMENTO_TOTAL_GERACAO + 15 s`. Alternativa: front sem timeout, descartada porque trava a interface se o backend morrer.
3. **Aquecimento via `keep_alive`.** No startup, o backend chama o Ollama com prompt vazio e `keep_alive` configurável (padrão 30 min). Isso testa a hipótese dos timeouts iniciais sem mudar o modelo.
4. **Fakes dos testes aceitam a assinatura real.** O `except TypeError` em `backend/servico.py` existe só porque os fakes não aceitam o parâmetro da API key. A correção é ajustar os fakes, não o código de produção.
5. **Marcadores de seção no arquivo importado.** Formato aceito: linhas `# História` e `# Critérios` (sem diferenciar maiúsculas e acentos). Substitui a heurística por palavras que gerou o bug 2.
6. **Testes da interface** com `streamlit.testing.v1.AppTest`, que roda o app sem navegador.

## Risks / Trade-offs

- [O aquecimento não resolve os timeouts] → Registrar a duração de cada tentativa e, se persistir, avaliar modelo menor ou quantização diferente no change de melhoria do modelo.
- [Mudança de formato do arquivo importado quebra arquivos antigos] → Mensagem de erro mostra um exemplo do formato aceito.

## Open Questions

- Valor padrão do orçamento total (180 s é o atual). Pode ser ajustado depois de medir com o aquecimento ativo.
