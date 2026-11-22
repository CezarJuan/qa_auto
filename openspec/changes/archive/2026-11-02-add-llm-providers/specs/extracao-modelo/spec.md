# Spec Delta

## MODIFIED Requirements

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
