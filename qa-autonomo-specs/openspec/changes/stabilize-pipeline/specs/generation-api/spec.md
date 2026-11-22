# Spec Delta

## Purpose

Definir o contrato HTTP entre interface e backend para gerar o modelo de estados e verificar a saúde do sistema, incluindo erros e limites de tempo.

## ADDED Requirements

### Requirement: Endpoint de geração
O endpoint `/gerar` SHALL receber a história e os critérios numerados e SHALL devolver o modelo de estados, o diagrama, o número de tentativas usadas e a duração total.

#### Scenario: Geração bem-sucedida
- **WHEN** a interface envia um requisito válido
- **THEN** a resposta tem status 200 com modelo, diagrama, tentativas e duração

### Requirement: Códigos de erro padronizados
A API SHALL responder 422 para entrada inválida, 502 para falha do provedor de LLM, 504 para orçamento de tempo esgotado e 500 para erro interno, sempre com corpo JSON contendo código e mensagem legível.

#### Scenario: Provedor sem API key
- **WHEN** o provedor é Gemini e a API key não está configurada
- **THEN** a resposta é 502 com mensagem que cita a API key ausente

#### Scenario: Erro interno inesperado
- **WHEN** ocorre uma exceção não prevista no backend
- **THEN** a resposta é 500 com corpo JSON contendo código e mensagem

### Requirement: Orçamento de tempo único
O backend SHALL respeitar um orçamento total de tempo por geração, somando todas as tentativas, e a interface SHALL aguardar no mínimo esse orçamento mais uma margem, lido da mesma configuração.

#### Scenario: Três tentativas lentas
- **WHEN** o orçamento é 180 s e as tentativas somadas passariam disso
- **THEN** o backend encerra com 504 antes de 180 s
- **AND** a interface ainda está aguardando e mostra a mensagem do 504

### Requirement: Erros sempre tratados pela interface
A interface SHALL mostrar mensagem legível para qualquer resposta de erro, inclusive corpo não JSON, e SHALL NOT exibir exceção ou stack trace ao usuário.

#### Scenario: Resposta 500 em texto puro
- **WHEN** o backend responde 500 com corpo "Internal Server Error"
- **THEN** a interface mostra "Erro interno no servidor" e o status 500

#### Scenario: Backend desligado
- **WHEN** a interface não consegue conectar ao backend
- **THEN** a interface informa que o backend está indisponível e como iniciá-lo

### Requirement: Endpoint de saúde
O endpoint `/saude` SHALL informar se o backend está ativo, qual provedor e modelo estão configurados e se o modelo está disponível.

#### Scenario: Consulta de saúde
- **WHEN** a interface consulta `/saude`
- **THEN** recebe provedor, modelo e disponibilidade do modelo
