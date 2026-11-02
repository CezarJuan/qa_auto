# generation-api Specification

## Purpose

Definir o contrato HTTP entre interface e backend para extrair o modelo de estados e verificar a saúde do sistema, incluindo erros e limites de tempo.

## Requirements

### Requirement: Endpoint de geração
O endpoint `/gerar` SHALL receber a história, os critérios numerados, o provedor e o sistema alvo opcional, e SHALL devolver o modelo de estados, a lista de tentativas com duração, resultado e erros, a duração total e a versão do prompt, o provedor e o modelo usados.

#### Scenario: Geração bem-sucedida
- **WHEN** a interface envia um requisito válido
- **THEN** a resposta tem status 200 com o modelo, as tentativas, a duração e a versão do prompt

#### Scenario: Falha após todas as tentativas
- **WHEN** as tentativas se esgotam com modelos inválidos
- **THEN** a resposta é 422 e o corpo inclui os erros da última tentativa

### Requirement: Códigos de erro padronizados
A API SHALL responder 422 para entrada ou modelo inválido, 502 para falha do provedor de LLM, 504 para orçamento de tempo esgotado e 500 para erro interno, sempre com corpo JSON contendo um código e uma mensagem legível.

#### Scenario: Provedor sem API key
- **WHEN** o provedor é Gemini e nenhuma API key está configurada
- **THEN** a resposta é 502 com mensagem que cita a API key ausente

#### Scenario: Erro de validação da entrada
- **WHEN** a requisição tem os critérios vazios
- **THEN** a resposta é 422 com código e mensagem em texto, não uma lista de erros internos

#### Scenario: Erro interno inesperado
- **WHEN** ocorre uma exceção não prevista no backend
- **THEN** a resposta é 500 com corpo JSON contendo código e mensagem

### Requirement: Orçamento de tempo único
O backend SHALL respeitar um orçamento total de tempo por geração, somando todas as tentativas, e SHALL não iniciar uma tentativa que não caiba no restante. A interface SHALL aguardar esse orçamento mais uma margem, lido da mesma configuração.

#### Scenario: Tentativas lentas
- **WHEN** o orçamento é 180 s e as tentativas somadas passariam disso
- **THEN** o backend encerra com 504 antes de 180 s mais o tempo de uma resposta
- **AND** a interface ainda está aguardando e mostra a mensagem do 504

### Requirement: Erros sempre tratados pela interface
A interface SHALL mostrar mensagem legível para qualquer resposta de erro, inclusive com corpo não JSON, e SHALL NOT exibir exceção ou stack trace ao usuário.

#### Scenario: Resposta 500 em texto puro
- **WHEN** o backend responde 500 com corpo "Internal Server Error"
- **THEN** a interface mostra "Erro interno no servidor" e o status 500

#### Scenario: Backend desligado
- **WHEN** a interface não consegue conectar ao backend
- **THEN** a interface informa que o backend está indisponível e como iniciá-lo

### Requirement: Endpoint de saúde
O endpoint `/saude` SHALL informar se o backend está ativo, o modelo configurado de cada provedor, se o modelo do Ollama está disponível e se há API key do Gemini configurada, sem expor a chave.

#### Scenario: Consulta de saúde
- **WHEN** a interface consulta `/saude`
- **THEN** recebe o modelo de cada provedor, a disponibilidade do modelo do Ollama e se a chave do Gemini existe
