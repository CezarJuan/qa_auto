# Design

## Context

Ver proposal.md (Why). `add-mbt-generator` entrega `.feature`, `test_<slug>.py`, `conftest.py` e um adaptador com três operações. O adaptador de simulação do modelo já existe, mas não serve como sistema alvo principal: testar o modelo contra ele mesmo é tautológico.

## Goals / Non-Goals

**Goals:**
- Evidência quantitativa para os Resultados Esperados do 5W2H: cobertura de borda, detecção de defeitos e tempo vs. QA humano.

**Non-Goals:**
- Executar testes contra sistemas externos via HTTP ou UI.
- Mutação automática de código (mutmut etc.); os mutantes são escritos à mão e documentados.

## Decisions

### 1. Sistemas de referência como classes Python pequenas

```
sistemas_referencia/
  saque_atm/
    correto.py            # class CaixaEletronico: inserir_cartao(), informar_pin(pin), sacar(valor)...
    mutantes/
      m1_retem_no_primeiro_erro.py
      m2_aceita_valor_acima_do_saldo.py
    adaptador.py          # traduz disparar("pin_invalido") → informar_pin(<pin errado>), etc.
    mutantes.yaml         # id, descrição, critério violado
  cupom_promocional/ ...
  mfa_bloqueio/ ...
  carrinho/ ...
```

Cada mutante é cópia do correto com uma alteração. O adaptador recebe a classe por injeção, e é assim que o executor troca correto por mutante. Alternativa: usar o modelo gabarito interpretado como sistema alvo. Descartada como alvo principal porque os testes vêm do mesmo tipo de modelo, mas continua sendo usada para testar o gerador.

### 2. Execução via `pytest --junitxml` em subprocesso

`subprocess.run([sys.executable, "-m", "pytest", pasta, "--junitxml", saida], timeout=...)`, com variável de ambiente que indica qual implementação o `conftest.py` deve carregar. O JUnit XML é nativo do pytest, sem dependência nova. O mapeamento cenário → critérios vem do `.feature` parseado (tags), cruzado pelo nome do cenário.

### 3. Suíte manual usando o mesmo vocabulário de passos

A suíte manual é um `.feature` escrito pelo grupo com as seis frases do vocabulário fixo. Assim ela roda com as mesmas definições de passo, e a comparação mede a qualidade dos cenários, não diferenças de infraestrutura. O tempo de elaboração é cronometrado e registrado em `suite_manual/<slug>/metadados.yaml`. Para ser justa, a suíte manual deve ser escrita **antes** de ver a suíte gerada, por um integrante que não implementou os mutantes.

### 4. Métricas para o relatório final

| Métrica | Fonte |
|---|---|
| Taxa de mutantes detectados (gerada vs manual) | análise de mutantes |
| Cenários de borda | tag `@borda` vs contagem manual |
| Tempo de elaboração | metadados manual vs duração da geração |
| Falsos alarmes | suíte do modelo extraído contra o sistema correto |

A meta de "produtividade superior a 70%" do 5W2H é calculada como `1 − tempo_gerado / tempo_manual`.

## Risks / Trade-offs

- [Mutantes fáceis demais inflam o resultado] → Ao menos um mutante por exemplo deve mexer em fronteira (ex.: `<` no lugar de `<=`), não só em fluxo.
- [Viés na suíte manual] → Regras da decisão 3 (escrever antes, pessoa diferente).
- [Adaptador mal escrito gera falha falsa] → A suíte do gabarito precisa passar 100% no sistema correto antes de qualquer medição (cenário da spec).
