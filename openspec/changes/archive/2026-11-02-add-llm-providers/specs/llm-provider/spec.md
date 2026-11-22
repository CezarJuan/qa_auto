# Spec Delta

## MODIFIED Requirements

### Requirement: Escolha do provedor e do modelo
A interface SHALL permitir escolher, em cada geração, um provedor do registro (Ollama, Gemini, compatível com OpenAI ou Anthropic) e, opcionalmente, o modelo. Sem modelo informado, SHALL valer o modelo da variável de ambiente do provedor, com padrão `llama3.1:8b` para o Ollama e `claude-opus-5-5` para a Anthropic, e o `.env.example` SHALL usar nomes de modelo explícitos.

#### Scenario: Ollama sem variável definida
- **WHEN** o provedor Ollama é usado sem `OLLAMA_MODEL` definida e sem modelo na requisição
- **THEN** a chamada usa o modelo `llama3.1:8b`

#### Scenario: Gemini selecionado
- **WHEN** o usuário escolhe Gemini e há API key configurada ou informada na interface
- **THEN** as chamadas de extração vão para o Gemini

#### Scenario: Modelo informado na requisição
- **WHEN** o usuário escolhe Ollama e informa o modelo `qwen2.5:7b`
- **THEN** a chamada usa `qwen2.5:7b`, mesmo com `OLLAMA_MODEL` definida com outro valor

#### Scenario: Anthropic sem variável definida
- **WHEN** o provedor Anthropic é usado sem `ANTHROPIC_MODEL` definida e sem modelo na requisição
- **THEN** a chamada usa o modelo `claude-opus-5-5`

## ADDED Requirements

### Requirement: Registro de provedores
O sistema SHALL manter um registro de provedores em que cada um declara id, nome de exibição, modelo configurado, se está configurado e se aceita saída restrita a JSON Schema, temperatura e semente. Interface, API e avaliação SHALL listar os provedores a partir desse registro.

#### Scenario: Provedores disponíveis
- **WHEN** o registro é consultado
- **THEN** ele contém `ollama`, `gemini`, `openai_compat` e `anthropic`, cada um com nome de exibição e capacidades

#### Scenario: Provedor desconhecido
- **WHEN** a geração é pedida com o provedor `fantasma`
- **THEN** a requisição é recusada citando o provedor e os ids aceitos, sem chamar nenhum LLM

### Requirement: Provedor compatível com OpenAI
O provedor `openai_compat` SHALL chamar qualquer servidor que implemente o protocolo de chat da OpenAI, usando URL base, chave e modelo configuráveis, e SHALL enviar o JSON Schema do modelo de estados conforme o modo configurado: esquema estrito, JSON livre ou nenhum.

#### Scenario: Servidor local sem chave
- **WHEN** a URL base aponta para um servidor local e nenhuma chave está configurada
- **THEN** a chamada é feita sem chave e o resultado passa pela mesma validação dos outros provedores

#### Scenario: Servidor sem suporte a esquema
- **WHEN** o modo de esquema configurado é JSON livre
- **THEN** a chamada pede JSON sem enviar o esquema, e a validação do modelo continua obrigatória

#### Scenario: URL base ausente
- **WHEN** o provedor é escolhido sem URL base configurada
- **THEN** a geração falha com mensagem de configuração que cita a variável ausente, sem chamar o servidor

### Requirement: Provedor Anthropic
O provedor `anthropic` SHALL chamar a API da Anthropic pelo SDK oficial, restringindo a saída ao JSON Schema do modelo de estados, e SHALL NOT enviar temperatura nem semente quando o modelo não as aceitar.

#### Scenario: Saída estruturada
- **WHEN** a extração é feita com o provedor Anthropic
- **THEN** a chamada envia o esquema do modelo de estados como formato de saída
- **AND** não envia temperatura nem semente para `claude-opus-5-5`

#### Scenario: Sem chave configurada
- **WHEN** o provedor Anthropic é escolhido e nenhuma credencial está disponível
- **THEN** a geração falha com mensagem que cita `ANTHROPIC_API_KEY`, sem fazer a chamada

### Requirement: Recusa do modelo
Quando o provedor encerrar a resposta por recusa de segurança, o sistema SHALL tratar a tentativa como falha do provedor, com a categoria da recusa na mensagem, e SHALL NOT validar o conteúdo como modelo de estados.

#### Scenario: Resposta recusada
- **WHEN** a Anthropic responde com motivo de parada `refusal`
- **THEN** a geração falha como erro do provedor, informando que o modelo recusou a solicitação

### Requirement: Erros transitórios do provedor
Sobrecarga, limite de taxa e indisponibilidade do provedor SHALL ser informados com mensagem que identifica o provedor e o tipo de falha, e nenhuma nova tentativa automática do cliente SHALL ultrapassar o orçamento de tempo da geração.

#### Scenario: Limite de taxa
- **WHEN** o provedor responde 429
- **THEN** a geração falha como erro do provedor, com mensagem que cita o limite de taxa e o provedor

#### Scenario: Provedor sobrecarregado
- **WHEN** a Anthropic responde que está sobrecarregada
- **THEN** a geração falha como erro do provedor, com mensagem que sugere tentar de novo ou trocar de provedor

### Requirement: Disponibilidade de cada provedor
Na verificação de saúde, o sistema SHALL informar para cada provedor se está configurado, qual modelo usaria e, quando aplicável, se o servidor responde, sem expor chaves.

#### Scenario: Provedor compatível sem URL
- **WHEN** `OPENAI_COMPAT_BASE_URL` não está definida
- **THEN** a verificação de saúde indica o provedor `openai_compat` como não configurado

#### Scenario: Chave nunca exposta
- **WHEN** `ANTHROPIC_API_KEY` está definida
- **THEN** a verificação de saúde informa que a chave existe, sem conter o valor dela
