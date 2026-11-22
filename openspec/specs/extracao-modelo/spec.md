# extracao-modelo Specification

## Purpose

Define como requisitos em linguagem natural viram um modelo de estados válido, restrito ao catálogo do sistema alvo quando houver um, e seguro para gerar grafos e testes.

## Requirements

### Requirement: Seleção do sistema alvo
A geração do modelo MUST aceitar um id opcional de sistema exemplo e, sem ele, extrair o modelo com nomes livres.

#### Scenario: Sistema informado
- **WHEN** a geração é solicitada com um id de sistema válido
- **THEN** a extração usa o catálogo desse sistema

#### Scenario: Sistema não informado
- **WHEN** a geração é solicitada sem id de sistema
- **THEN** a extração ocorre sem catálogo e as regras gerais de validação continuam valendo

#### Scenario: Sistema desconhecido
- **WHEN** a geração é solicitada com um id inexistente
- **THEN** a API responde 422 com mensagem que identifica o id, sem chamar o LLM

### Requirement: Catálogo enviado ao LLM
Quando houver sistema alvo, o prompt MUST incluir os estados, eventos e variáveis do catálogo com suas descrições, o estado inicial e a instrução de usar somente esses nomes.

#### Scenario: Prompt com catálogo
- **WHEN** o LLM é chamado para um sistema alvo
- **THEN** a mensagem enviada contém cada estado, evento e variável do catálogo e o estado inicial

#### Scenario: Catálogo sem variáveis
- **WHEN** o catálogo do sistema alvo não declara variáveis
- **THEN** o prompt instrui o LLM a não declarar variáveis

### Requirement: Conformidade com o catálogo
Quando houver sistema alvo, a validação MUST rejeitar modelos com id de estado, evento ou variável fora do catálogo, ou com estado inicial diferente do definido no catálogo.

#### Scenario: Nome fora do catálogo
- **WHEN** o modelo usa um evento, estado ou variável que não está no catálogo
- **THEN** a validação falha indicando o nome e o erro é devolvido ao LLM na próxima tentativa

#### Scenario: Estado inicial divergente
- **WHEN** o estado do tipo inicial no modelo difere do estado inicial do catálogo
- **THEN** a validação falha indicando os dois valores

### Requirement: Critérios numerados na entrada
A API MUST recusar requisições cujos critérios de aceite não tenham nenhuma linha numerada.

#### Scenario: Critérios sem numeração
- **WHEN** os critérios são enviados como uma lista sem números
- **THEN** a API responde 422 com mensagem pedindo a numeração, sem chamar o LLM

### Requirement: Saída restrita ao esquema
A chamada de extração MUST restringir a saída do LLM ao JSON Schema do modelo de estados quando o provedor suportar, e MUST usar temperatura 0 e semente fixa configurável quando o provedor aceitar esses parâmetros. Quando não aceitar, MUST omiti-los e registrar no resultado que a extração não é determinística.

#### Scenario: Extração com Ollama
- **WHEN** a extração é feita com Ollama
- **THEN** a chamada envia o JSON Schema do modelo como formato de saída
- **AND** usa temperatura 0 e a semente configurada

#### Scenario: Provedor sem temperatura
- **WHEN** a extração é feita com um modelo que recusa temperatura e semente
- **THEN** a chamada envia o JSON Schema sem esses parâmetros
- **AND** o resultado registra que a extração não é determinística

### Requirement: Prompt com critérios numerados e exemplo resolvido
O prompt MUST conter a história, os critérios numerados, a descrição das linguagens de guarda e ação e ao menos um exemplo completo de entrada e modelo esperado.

#### Scenario: Montagem do prompt
- **WHEN** a extração é chamada com 3 critérios
- **THEN** o prompt contém os critérios numerados 1, 2 e 3, as linguagens de guarda e ação e um exemplo resolvido

### Requirement: Correção guiada por erros
Quando o modelo extraído falhar no esquema ou na validação, o sistema MUST pedir uma nova versão ao LLM enviando o modelo anterior e todos os erros encontrados, até o limite de tentativas e dentro do orçamento de tempo.

#### Scenario: Critério não coberto na primeira tentativa
- **WHEN** a primeira resposta não cobre o critério 2
- **THEN** a segunda chamada inclui o modelo anterior e a mensagem de que o critério 2 não está representado

#### Scenario: Limite de tentativas
- **WHEN** as 3 tentativas falham na validação
- **THEN** a geração termina com erro e devolve os erros da última tentativa

### Requirement: Registro das tentativas
O resultado da extração MUST incluir, para cada tentativa, a duração, o resultado (válido, inválido ou timeout) e os erros de validação.

#### Scenario: Sucesso na segunda tentativa
- **WHEN** a primeira tentativa é inválida e a segunda é válida
- **THEN** o resultado lista as duas tentativas com as durações e os erros da primeira

### Requirement: Prompt versionado
O sistema MUST identificar a versão do prompt e dos exemplos usados em cada extração e incluí-la no resultado, junto com o provedor e o modelo.

#### Scenario: Versão no resultado
- **WHEN** uma extração termina
- **THEN** o resultado informa a versão do prompt, o provedor e o modelo usados
