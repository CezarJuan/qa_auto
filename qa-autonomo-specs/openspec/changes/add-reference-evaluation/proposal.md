# Proposal

## Why

O explore encontrou três modelos que passaram na validação e estavam semanticamente errados (um único PIN errado retinha o cartão; dava para finalizar a compra com o carrinho vazio). A validação estrutural não detecta isso. Sem casos de referência e métricas, não há como saber se trocar de modelo, adicionar few-shot ou fazer fine-tuning no Ollama melhora ou piora a extração. Este change também é o passo 8 do 5W2H: avaliação experimental.

## What Changes

- Conjunto de casos de referência versionado: entrada, modelo gabarito e propriedades comportamentais verificáveis, separado em desenvolvimento e teste.
- Executor de avaliação por linha de comando que roda a extração N vezes por caso em uma configuração (provedor, modelo, versão do prompt) e calcula métricas.
- Métricas: validade, tentativas, latência, precisão e recall de estados e transições após alinhamento de nomes, e taxa de propriedades satisfeitas.
- Relatório por execução e comparação entre configurações.

## Capabilities

### New Capabilities
- `reference-cases`: conjunto versionado de histórias com modelo gabarito e propriedades esperadas.
- `extraction-evaluation`: execução da extração contra os casos de referência, cálculo de métricas e comparação entre configurações.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- Novo diretório `benchmark/` (casos) e módulo `avaliacao/` (executor e métricas).
- Reusa o interpretador de guardas e ações de `fsm-model-v2`.
- Não altera a interface web nem a API.
- Pré-requisito para o change de melhoria do modelo do Ollama.
