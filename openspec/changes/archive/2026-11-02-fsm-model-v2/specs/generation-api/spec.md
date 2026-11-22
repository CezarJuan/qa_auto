# Spec Delta

## MODIFIED Requirements

### Requirement: Endpoint de geração
O endpoint `/gerar` SHALL receber a história, os critérios numerados, o provedor e o sistema alvo opcional, e SHALL devolver o modelo de estados, a lista de tentativas com duração, resultado e erros, a duração total e a versão do prompt, o provedor e o modelo usados.

#### Scenario: Geração bem-sucedida
- **WHEN** a interface envia um requisito válido
- **THEN** a resposta tem status 200 com o modelo, as tentativas, a duração e a versão do prompt

#### Scenario: Falha após todas as tentativas
- **WHEN** as tentativas se esgotam com modelos inválidos
- **THEN** a resposta é 422 e o corpo inclui os erros da última tentativa
