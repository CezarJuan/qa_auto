# Spec Delta

## Purpose

Configurar e chamar o provedor de LLM usado na extração, com Ollama local como padrão gratuito e Gemini como alternativa, e informar com clareza quando o provedor não está utilizável.

## ADDED Requirements

### Requirement: Seleção de provedor por configuração
O sistema SHALL selecionar o provedor (Ollama ou Gemini) e o nome do modelo por variáveis de ambiente, com Ollama como padrão. O `.env.example` SHALL usar um nome de modelo com tag explícita.

#### Scenario: Configuração padrão
- **WHEN** nenhuma variável de provedor está definida
- **THEN** o sistema usa o Ollama no endereço local padrão

#### Scenario: Gemini selecionado
- **WHEN** o provedor configurado é Gemini e há API key
- **THEN** as chamadas de extração vão para o Gemini

### Requirement: Verificação do modelo configurado
Na inicialização e em cada verificação de saúde, o sistema SHALL confirmar que o modelo configurado está disponível no provedor. Se não estiver, SHALL informar o nome configurado e os modelos disponíveis.

#### Scenario: Modelo sem a tag instalada
- **WHEN** o modelo configurado é "llama3.1" e o Ollama só tem "llama3.1:8b"
- **THEN** a verificação de saúde indica indisponível
- **AND** a mensagem cita "llama3.1" e lista "llama3.1:8b" como disponível

### Requirement: Falha de configuração não gera nova chamada
Erros de configuração ou erros internos de programação SHALL interromper a geração com mensagem de erro e SHALL NOT disparar uma nova chamada ao provedor com parâmetros diferentes, como sem API key.

#### Scenario: Erro interno durante a chamada
- **WHEN** a chamada ao provedor lança um erro de tipo interno
- **THEN** a geração falha com mensagem de erro interno
- **AND** nenhuma segunda chamada é feita ao provedor

### Requirement: Aquecimento do modelo local
Quando o provedor for Ollama, o sistema SHALL carregar o modelo na memória antes da primeira geração e mantê-lo carregado por um período configurável.

#### Scenario: Primeira geração após iniciar
- **WHEN** o backend inicia com Ollama configurado
- **THEN** o modelo é carregado antes de a interface liberar o envio
- **AND** a interface mostra "carregando modelo" enquanto isso

### Requirement: Tempo limite por chamada
Cada chamada ao provedor SHALL ter tempo limite configurável. Ao estourar, a tentativa SHALL ser registrada como timeout, distinta de resposta inválida.

#### Scenario: Chamada lenta
- **WHEN** o provedor não responde dentro do tempo limite
- **THEN** a tentativa é encerrada e registrada como timeout
