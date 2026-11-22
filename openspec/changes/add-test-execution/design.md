# Design

## Context

Ver proposal.md (Why). Estado esperado após `add-mbt-generator`:

- `sistemas_exemplo/` tem Login e Saque, com `correto` e `bug` (subclasse que sobrescreve um método), catálogo, modelo de referência e a interface do adaptador (`definir_contexto`, `disparar(evento, dados) -> bool`, `estado_atual`).
- O pacote gerado tem `.feature`, teste, adaptador e `conftest.py`. O adaptador escolhe a variante por `QA_VARIANTE`.
- `backend/execucao.py` roda duas variantes em subprocesso, lê o JUnit XML e calcula o veredito pela tabela do change arquivado.
- `exemplos/` tem os gabaritos de `saque-atm`, `cupom-promocional`, `mfa-bloqueio` e `carrinho`.

O material original previa um diretório novo `sistemas_referencia/`. Como `sistemas_exemplo/` já cumpre esse papel, este change o estende em vez de criar um paralelo.

## Goals / Non-Goals

**Goals:**
- Evidência quantitativa para os Resultados Esperados do 5W2H: cobertura de borda, detecção de defeitos e tempo em comparação com o QA humano.

**Non-Goals:**
- Executar testes contra sistemas externos via HTTP ou UI.
- Mutação automática de código (mutmut etc.). Os mutantes são escritos à mão e documentados.

## Decisions

### 1. Mutantes como subclasses com uma sobrescrita

```
sistemas_exemplo/
  saque_atm.py      # catálogo, SaqueAtm, mutantes, referência, requisitos
  cupom.py
  mfa.py
  carrinho.py
  login.py
  mutantes.yaml     # por sistema: id, descrição, critério, tipo (fluxo|fronteira)
```

Cada mutante é uma subclasse da correta que sobrescreve um único método de regra, como já é feito com `LoginComBug`. Isso torna a "única alteração" verificável por inspeção do diff da classe. `criar(id, variante)` aceita `correto` ou o id do mutante. Para compatibilidade, `bug` é um alias do primeiro mutante. Alternativa descartada: cópia inteira do arquivo por mutante, que dificulta revisar o que mudou.

O Saque ATM substitui o Saque atual. A contagem de PINs passa a ser variável de estado no modelo de referência, como no gabarito de `fsm-model-v2`. O catálogo declara `valor` (entrada), `saldo` (contexto) e `tentativas` (estado).

### 2. Execução contra N alvos

`executar_testes(artefatos, sistema)` roda o pacote uma vez por variante (`correto` + mutantes), com `QA_VARIANTE` e tempo limite configurável (padrão 60 s por variante), e devolve um `ResultadoVariante` por alvo. O mapeamento cenário → critérios vem das tags do `.feature`, lidas com `gherkin-official` e cruzadas pelo nome do cenário no JUnit XML.

### 3. Veredito

| Variante correta | Mutantes | Veredito |
|---|---|---|
| erro | qualquer | Erro de execução |
| falhou | qualquer | Modelo diverge do sistema (falsos alarmes) |
| passou | algum com erro | Erro de execução |
| passou | todos detectados | Bugs detectados (N de N) |
| passou | parte detectada | Bugs detectados parcialmente (k de N) |
| passou | nenhum detectado | Bug não detectado (0 de N) |

### 4. Suíte manual com o mesmo vocabulário de passos

A suíte manual é um `.feature` escrito pelo grupo com as seis frases do vocabulário fixo. Assim ela roda com as mesmas definições de passo, e a comparação mede a qualidade dos cenários, não diferenças de infraestrutura. O tempo de elaboração fica em `suite_manual/<slug>/metadados.yaml`. Para ser justa, a suíte manual deve ser escrita antes de ver a suíte gerada, por um integrante que não implementou os mutantes.

### 5. Métricas para o relatório final

| Métrica | Fonte |
|---|---|
| Taxa de mutantes detectados (gerada vs manual) | análise de mutantes |
| Cenários de borda | tag `@borda` vs contagem manual |
| Tempo de elaboração | metadados manual vs duração da geração |
| Falsos alarmes | suíte do modelo extraído contra a variante correta |

A meta de "produtividade superior a 70%" do 5W2H é calculada como `1 − tempo_gerado / tempo_manual`.

### 6. Linha de comando

`python -m backend.cli executar --pacote dir --sistema id [--timeout s]` e `python -m backend.cli comparar --sistema id`, reusando `backend/execucao.py`.

## Risks / Trade-offs

- [Mutantes fáceis demais inflam o resultado] → Ao menos um mutante por sistema mexe em fronteira (ex.: `<` no lugar de `<=`), não só em fluxo.
- [Viés na suíte manual] → Regras da decisão 4: escrever antes e por outra pessoa.
- [Adaptador mal escrito gera falha falsa] → A suíte do modelo de referência precisa passar 100% na variante correta antes de qualquer medição.
- [Tempo total cresce com o número de mutantes] → Tempo limite por variante e execução sequencial com progresso na interface. Paralelizar fica como melhoria.

## Migration Plan

O id `saque` deixa de existir e passa a ser `saque-atm`. Exemplos, demonstração e testes são atualizados no mesmo change. A variante `bug` continua aceita como alias. Para reverter, basta desfazer o merge.
