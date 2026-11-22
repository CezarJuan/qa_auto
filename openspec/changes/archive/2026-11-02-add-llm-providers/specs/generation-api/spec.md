# Spec Delta

## MODIFIED Requirements

### Requirement: Endpoint de geração
O endpoint `/gerar` SHALL receber a história, os critérios numerados, o provedor (id do registro ou rótulo legado), o modelo opcional e o sistema alvo opcional. SHALL devolver o modelo de estados, a lista de tentativas com duração, resultado e erros, a duração total, a versão do prompt, o provedor e o modelo usados e se a extração foi determinística.

#### Scenario: Geração bem-sucedida
- **WHEN** a interface envia um requisito válido
- **THEN** a resposta tem status 200 com o modelo, as tentativas, a duração e a versão do prompt

#### Scenario: Falha após todas as tentativas
- **WHEN** as tentativas se esgotam com modelos inválidos
- **THEN** a resposta é 422 e o corpo inclui os erros da última tentativa

#### Scenario: Rótulo legado do provedor
- **WHEN** a requisição usa o motor "Ollama (Local)"
- **THEN** a geração usa o provedor `ollama`, como antes

#### Scenario: Extração não determinística
- **WHEN** a geração usa um provedor que não aceita temperatura nem semente
- **THEN** a resposta informa que a extração não foi determinística

### Requirement: Endpoint de saúde
O endpoint `/saude` SHALL informar se o backend está ativo e, para cada provedor do registro, se está configurado, o modelo que usaria e sua disponibilidade, incluindo o modelo do Ollama e o aquecimento, sem expor chaves.

#### Scenario: Consulta de saúde
- **WHEN** a interface consulta `/saude`
- **THEN** recebe uma entrada por provedor com configuração, modelo e disponibilidade
- **AND** a entrada do Ollama mantém a disponibilidade do modelo e a situação do aquecimento
