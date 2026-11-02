# Proposal

## Why

O explore apontou que, sem um sistema alvo, "gerar testes" produz só esqueleto. Para provar a tese do 5W2H (cobertura maior e testes que detectam defeitos), os testes gerados precisam rodar contra algo real: um sistema correto, em que devem passar, e versões com defeito, em que devem falhar. Isso também permite a comparação com testes escritos à mão prevista em Resultados Esperados.

## What Changes

- Sistemas de referência para os exemplos canônicos (Saque, Cupom, MFA e Carrinho): uma implementação correta e mutantes com defeitos documentados, incluindo os erros que o LLM cometeu no explore.
- Execução da suíte gerada contra um sistema escolhido, isolada e com tempo limite, pela interface e pela linha de comando.
- Relatório por cenário e por critério de aceite, taxa de mutantes detectados e falsos alarmes contra o sistema correto.
- Comparação com uma suíte escrita à mão para os mesmos exemplos: tempo de elaboração, número de cenários, cenários de borda e mutantes detectados.

## Capabilities

### New Capabilities
- `reference-systems`: implementações de referência corretas e mutantes dos exemplos canônicos, usadas como sistema sob teste.
- `test-execution`: execução das suítes geradas, relatório de resultados, análise de mutantes e comparação com suíte manual.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- Novo diretório `sistemas_referencia/` e módulo de execução.
- Nova aba "Execução" na interface.
- Usa os artefatos e o adaptador de `add-mbt-generator`.
- Exige que o grupo escreva uma suíte manual para os 3 exemplos canônicos e registre o tempo gasto.
