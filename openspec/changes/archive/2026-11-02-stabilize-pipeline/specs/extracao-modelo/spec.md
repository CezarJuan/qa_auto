# Spec Delta

## REMOVED Requirements

### Requirement: Limites de tempo configuráveis
**Reason**: O limite "por chamada × número de tentativas" é substituído por um orçamento total por geração, compartilhado entre interface e backend (bug 5).
**Migration**: O tempo limite por chamada passa para `llm-provider` ("Tempo limite por chamada"), e a espera da interface passa para `generation-api` ("Orçamento de tempo único").

### Requirement: Modelo Ollama padrão disponível
**Reason**: A configuração dos provedores ganha uma capability própria.
**Migration**: O padrão `llama3.1:8b` continua valendo em `llm-provider` ("Escolha do provedor e do modelo").
