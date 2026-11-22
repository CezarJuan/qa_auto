# Spec Delta

## Purpose

Extrair, com um LLM, o modelo de estados de uma história de usuário e seus critérios, de forma estruturada, reproduzível e corrigida pelos erros de validação.

## ADDED Requirements

### Requirement: Saída restrita ao esquema
A chamada de extração SHALL restringir a saída do LLM ao JSON Schema do modelo de estados, quando o provedor suportar, e SHALL usar temperatura zero e semente fixa.

#### Scenario: Extração com Ollama
- **WHEN** a extração é feita com Ollama
- **THEN** a chamada envia o JSON Schema do modelo como formato de saída
- **AND** usa temperatura 0 e semente configurada

### Requirement: Prompt com critérios numerados e exemplos
O prompt SHALL conter a história, os critérios numerados, a descrição das linguagens de guarda e ação e ao menos um exemplo completo de entrada e modelo esperado.

#### Scenario: Montagem do prompt
- **WHEN** a extração é chamada com 3 critérios
- **THEN** o prompt contém os critérios numerados 1, 2 e 3 e um exemplo resolvido

### Requirement: Correção guiada por erros
Quando o modelo extraído falhar no esquema ou na validação, o sistema SHALL pedir nova versão ao LLM enviando os erros encontrados, até o limite configurado de tentativas e dentro do orçamento de tempo.

#### Scenario: Critério não coberto na primeira tentativa
- **WHEN** a primeira resposta não cobre o critério 2
- **THEN** a segunda chamada inclui a mensagem de que o critério 2 não está representado

#### Scenario: Limite de tentativas
- **WHEN** as 3 tentativas falham na validação
- **THEN** a geração termina com erro e devolve os erros da última tentativa

### Requirement: Registro das tentativas
O resultado da extração SHALL incluir, para cada tentativa, a duração, o resultado (válido, inválido ou timeout) e os erros de validação.

#### Scenario: Sucesso na segunda tentativa
- **WHEN** a primeira tentativa é inválida e a segunda é válida
- **THEN** o resultado lista as duas tentativas com durações e os erros da primeira

### Requirement: Prompt versionado
O sistema SHALL identificar a versão do prompt e dos exemplos usados em cada extração e incluí-la no resultado.

#### Scenario: Versão no resultado
- **WHEN** uma extração termina
- **THEN** o resultado informa a versão do prompt, o provedor e o modelo usados
