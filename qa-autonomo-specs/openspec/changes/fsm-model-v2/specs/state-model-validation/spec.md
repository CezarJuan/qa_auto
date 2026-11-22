# Spec Delta

## Purpose

Garantir que um modelo de estados só siga no pipeline quando for estruturalmente consistente, com mensagens de erro precisas o bastante para o LLM corrigir o modelo.

## ADDED Requirements

### Requirement: Estado inicial único
O modelo SHALL ter exatamente um estado do tipo inicial.

#### Scenario: Dois estados iniciais
- **WHEN** o modelo tem `Inicio` e `Login` como iniciais
- **THEN** a validação falha com erro citando os dois estados

### Requirement: Estados finais
O modelo SHALL ter ao menos um estado final, e estados finais SHALL NOT ter transições de saída.

#### Scenario: Laço em estado final
- **WHEN** existe transição de `CartaoRetido` (final) para `CartaoRetido`
- **THEN** a validação falha com erro dizendo que `CartaoRetido` é final e tem saída

#### Scenario: Nenhum estado final
- **WHEN** nenhum estado é do tipo final
- **THEN** a validação falha com erro pedindo ao menos um estado final

### Requirement: Alcançabilidade e término
Todo estado SHALL ser alcançável a partir do inicial e SHALL ter caminho até algum estado final.

#### Scenario: Estado inalcançável
- **WHEN** nenhuma transição chega a `Bloqueado`
- **THEN** a validação falha citando `Bloqueado` como inalcançável

#### Scenario: Estado sem saída que não é final
- **WHEN** `Processando` não tem saída e não é final
- **THEN** a validação falha citando `Processando` como beco sem saída

### Requirement: Referências válidas
Transições SHALL referenciar apenas estados declarados, e guardas e ações SHALL referenciar apenas variáveis declaradas e respeitar seus tipos.

#### Scenario: Variável não declarada
- **WHEN** a guarda é `saldo >= valor` e `saldo` não foi declarada
- **THEN** a validação falha citando a transição e a variável `saldo`

### Requirement: Critérios de aceite válidos e cobertos
Toda referência a critério SHALL apontar para um número de 1 a N da entrada, e cada critério de 1 a N SHALL aparecer em ao menos uma transição.

#### Scenario: Critério inexistente
- **WHEN** a entrada tem 4 critérios e uma transição cita o critério 99
- **THEN** a validação falha citando a transição e o critério 99

#### Scenario: Critério não coberto
- **WHEN** nenhuma transição cita o critério 2
- **THEN** a validação falha dizendo que o critério 2 não está representado

### Requirement: Determinismo das transições
Para cada par de estado e evento com mais de uma transição, todas SHALL ter guarda e nenhuma valoração analisada das variáveis SHALL satisfazer duas guardas ao mesmo tempo.

#### Scenario: Duas transições sem guarda
- **WHEN** `finalizar` sai de `ComItens` duas vezes sem guarda
- **THEN** a validação falha citando o par `ComItens` / `finalizar`

#### Scenario: Guardas sobrepostas
- **WHEN** as guardas são `tentativas < 3` e `tentativas >= 2`
- **THEN** a validação falha mostrando `tentativas = 2` como valor que satisfaz as duas

#### Scenario: Guardas complementares
- **WHEN** as guardas são `valor <= saldo` e `valor > saldo`
- **THEN** a validação aceita o par

### Requirement: Transições duplicadas
O modelo SHALL NOT ter duas transições com mesma origem, evento, guarda e destino.

#### Scenario: Transição repetida
- **WHEN** a transição `adicionar_item` de `Vazio` para `ComItens` aparece duas vezes
- **THEN** a validação falha citando as duas transições

### Requirement: Mensagens de erro para correção
Cada erro de validação SHALL ter um código, os elementos envolvidos e uma mensagem em português que diga o que corrigir, e a validação SHALL devolver todos os erros encontrados de uma vez.

#### Scenario: Vários erros
- **WHEN** um modelo tem um critério não coberto e um estado inalcançável
- **THEN** a validação devolve os dois erros na mesma resposta
