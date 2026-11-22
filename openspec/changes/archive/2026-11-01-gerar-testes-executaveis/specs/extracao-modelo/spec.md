# Spec Delta

## Purpose

Define como requisitos em linguagem natural viram um modelo de estados válido, restrito ao catálogo do sistema alvo quando houver um, e seguro para gerar grafos e testes.

## ADDED Requirements

### Requirement: Seleção do sistema alvo
A geração do modelo MUST aceitar um id opcional de sistema exemplo e, sem ele, extrair o modelo com nomes livres.

#### Scenario: Sistema informado
- **WHEN** a geração é solicitada com um id de sistema válido
- **THEN** a extração usa o catálogo desse sistema

#### Scenario: Sistema não informado
- **WHEN** a geração é solicitada sem id de sistema
- **THEN** a extração ocorre sem catálogo e as regras gerais de validação continuam valendo

#### Scenario: Sistema desconhecido
- **WHEN** a geração é solicitada com um id inexistente
- **THEN** a API responde 422 com mensagem que identifica o id, sem chamar o LLM

### Requirement: Catálogo enviado ao LLM
Quando houver sistema alvo, o prompt MUST incluir os estados e eventos do catálogo com suas descrições, o estado inicial e a instrução de usar somente esses nomes.

#### Scenario: Prompt com catálogo
- **WHEN** o LLM é chamado para um sistema alvo
- **THEN** a mensagem enviada contém cada estado e evento do catálogo e o estado inicial

### Requirement: Conformidade com o catálogo
Quando houver sistema alvo, a validação MUST rejeitar modelos com estado ou evento fora do catálogo, ou com estado inicial diferente do definido no catálogo.

#### Scenario: Nome fora do catálogo
- **WHEN** o modelo usa um evento ou estado que não está no catálogo
- **THEN** a validação falha indicando o nome e o erro é devolvido ao LLM na próxima tentativa

#### Scenario: Estado inicial divergente
- **WHEN** o estado inicial do modelo difere do estado inicial do catálogo
- **THEN** a validação falha indicando os dois valores

### Requirement: Nomes de estado seguros
A validação MUST rejeitar nomes de estado que não sejam compostos apenas por letras, dígitos e sublinhado, iniciando por letra.

#### Scenario: Estado com espaço
- **WHEN** o modelo contém o estado `Com itens`
- **THEN** a validação falha indicando o nome

#### Scenario: Estado com hífen
- **WHEN** o modelo contém o estado `Fim-Ok`
- **THEN** a validação falha indicando o nome

#### Scenario: Estado com acento
- **WHEN** o modelo contém o estado `ValidaçãoPIN`
- **THEN** o nome é aceito

### Requirement: Determinismo das transições
A validação MUST rejeitar duas transições com o mesmo estado de origem e o mesmo evento.

#### Scenario: Destinos diferentes
- **WHEN** um estado e um evento levam a dois destinos diferentes
- **THEN** a validação falha indicando o estado e o evento

#### Scenario: Transição repetida
- **WHEN** a mesma transição aparece duas vezes
- **THEN** a validação falha indicando a transição

### Requirement: Rastreabilidade de critérios
A validação MUST exigir que todo critério de aceite numerado apareça em ao menos uma transição e rejeitar transições que citem um número inexistente.

#### Scenario: Critério inexistente
- **WHEN** uma transição cita o critério 99 e os requisitos têm só o critério 1
- **THEN** a validação falha indicando o número 99

#### Scenario: Critério sem transição
- **WHEN** um critério numerado não aparece em nenhuma transição
- **THEN** a validação falha indicando o número

### Requirement: Critérios numerados na entrada
A API MUST recusar requisições cujos critérios de aceite não tenham nenhuma linha numerada.

#### Scenario: Critérios sem numeração
- **WHEN** os critérios são enviados como uma lista sem números
- **THEN** a API responde 422 com mensagem pedindo a numeração, sem chamar o LLM

### Requirement: Estados finais opcionais
O modelo MUST aceitar uma lista opcional de estados finais, e a validação MUST exigir que todos pertençam à lista de estados.

#### Scenario: Final desconhecido
- **WHEN** um estado final não está na lista de estados
- **THEN** a validação falha indicando o nome

#### Scenario: Modelo sem finais
- **WHEN** o modelo não informa estados finais
- **THEN** o modelo é aceito se as demais regras forem atendidas

#### Scenario: Final exibido no grafo
- **WHEN** o grafo de um modelo com estado final é exibido
- **THEN** o diagrama mostra a saída desse estado para o marcador de fim

### Requirement: Limites de tempo configuráveis
O tempo limite de cada chamada ao LLM MUST ser configurável por variável de ambiente, e a interface MUST aguardar o pior caso do backend, somando todas as tentativas.

#### Scenario: Timeout configurado
- **WHEN** a variável de timeout do LLM está definida
- **THEN** cada chamada ao motor usa esse valor

#### Scenario: Interface coerente com o backend
- **WHEN** o backend usa todas as tentativas e cada uma leva o tempo limite
- **THEN** a interface ainda está aguardando quando o backend responde

### Requirement: Modelo Ollama padrão disponível
A configuração padrão do Ollama MUST apontar para `llama3.1:8b`.

#### Scenario: Sem variável definida
- **WHEN** o motor Ollama é usado sem `OLLAMA_MODEL` definida
- **THEN** a chamada usa o modelo `llama3.1:8b`
