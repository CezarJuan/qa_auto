# llm-provider Specification

## Purpose

Configurar e chamar o provedor de LLM usado na extração (Ollama local ou Gemini) e informar com clareza quando o provedor não pode ser usado.

## Requirements

### Requirement: Escolha do provedor e do modelo
A interface SHALL permitir escolher o provedor (Ollama ou Gemini) em cada geração. O nome do modelo de cada provedor SHALL vir de variável de ambiente, com padrão `llama3.1:8b` para o Ollama, e o `.env.example` SHALL usar nomes de modelo com tag explícita.

#### Scenario: Ollama sem variável definida
- **WHEN** o provedor Ollama é usado sem `OLLAMA_MODEL` definida
- **THEN** a chamada usa o modelo `llama3.1:8b`

#### Scenario: Gemini selecionado
- **WHEN** o usuário escolhe Gemini e há API key configurada ou informada na interface
- **THEN** as chamadas de extração vão para o Gemini

### Requirement: Verificação do modelo configurado
Na inicialização do backend e em cada verificação de saúde, o sistema SHALL confirmar que o modelo configurado do Ollama está instalado. Se não estiver, SHALL informar o nome configurado e os modelos disponíveis.

#### Scenario: Modelo sem a tag instalada
- **WHEN** o modelo configurado é "llama3.1" e o Ollama só tem "llama3.1:8b"
- **THEN** a verificação de saúde indica o modelo como indisponível
- **AND** a mensagem cita "llama3.1" e lista "llama3.1:8b" como disponível

#### Scenario: Ollama desligado
- **WHEN** o servidor do Ollama não responde
- **THEN** a verificação de saúde indica o Ollama como inacessível, sem impedir o uso do Gemini

### Requirement: Falha de configuração não gera nova chamada
Erros de configuração ou de programação SHALL interromper a geração com mensagem de erro e SHALL NOT disparar uma nova chamada ao provedor com parâmetros diferentes, por exemplo sem API key.

#### Scenario: Erro interno durante a chamada
- **WHEN** a chamada ao provedor lança um erro de tipo interno
- **THEN** a geração falha com mensagem de erro interno
- **AND** nenhuma segunda chamada é feita ao provedor

### Requirement: Aquecimento do modelo local
Quando o Ollama estiver disponível, o backend SHALL carregar o modelo configurado na memória ao iniciar e mantê-lo carregado por um período configurável.

#### Scenario: Primeira geração após iniciar
- **WHEN** o backend inicia com o Ollama acessível
- **THEN** ele pede ao Ollama para carregar o modelo antes da primeira geração
- **AND** enquanto o carregamento não termina, `/saude` informa "carregando modelo"

### Requirement: Tempo limite por chamada
Cada chamada ao provedor SHALL ter um tempo limite configurável por variável de ambiente. Ao estourar, a tentativa SHALL ser registrada como timeout, distinta de resposta inválida.

#### Scenario: Timeout configurado
- **WHEN** a variável de tempo limite por chamada está definida
- **THEN** cada chamada ao provedor usa esse valor

#### Scenario: Chamada lenta
- **WHEN** o provedor não responde dentro do tempo limite
- **THEN** a tentativa é encerrada e registrada como timeout
