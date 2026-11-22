# Spec Delta

## Purpose

Receber a história de usuário e os critérios de aceite em português, por formulário, arquivo ou exemplo canônico, e entregá-los normalizados ao pipeline de extração.

## ADDED Requirements

### Requirement: Campos obrigatórios da entrada
A interface SHALL oferecer um campo para a história de usuário e outro para os critérios de aceite, e SHALL bloquear o envio quando um deles estiver vazio, indicando qual falta.

#### Scenario: Envio sem critérios
- **WHEN** o usuário envia a história sem nenhum critério de aceite
- **THEN** o envio é bloqueado
- **AND** a interface informa que os critérios de aceite são obrigatórios

#### Scenario: Envio completo
- **WHEN** o usuário preenche a história e ao menos um critério
- **THEN** o requisito é enviado para geração

### Requirement: Limite de tamanho da entrada
O sistema SHALL rejeitar história ou critérios com mais de 2000 caracteres cada, informando o tamanho atual e o limite antes de chamar o backend.

#### Scenario: Critérios acima do limite
- **WHEN** os critérios têm 2100 caracteres
- **THEN** o envio é bloqueado com a mensagem de que o limite é 2000 e a entrada tem 2100

### Requirement: Numeração dos critérios de aceite
A interface SHALL numerar os critérios de 1 a N na ordem em que aparecem, preservando a numeração do usuário quando ela já existir, e SHALL mostrar a lista numerada antes da geração.

#### Scenario: Critérios sem numeração
- **WHEN** o usuário digita três critérios em linhas separadas, sem números
- **THEN** o sistema envia e apresenta os critérios como 1, 2 e 3

#### Scenario: Critérios já numerados
- **WHEN** o usuário digita "1. ...", "2. ..." e "3. ..."
- **THEN** o sistema mantém os números 1, 2 e 3

### Requirement: Importação de arquivo de requisitos
O sistema SHALL importar a história e os critérios de um arquivo de texto usando os marcadores de seção `# História` e `# Critérios`, sem diferenciar maiúsculas nem acentos, e SHALL NOT descartar linhas por conterem palavras comuns como "cada".

#### Scenario: Linha de critério com a palavra "cada"
- **WHEN** o arquivo tem o critério "cada tentativa inválida incrementa o contador"
- **THEN** a linha é importada como critério de aceite

#### Scenario: Arquivo sem história
- **WHEN** o arquivo não contém a seção da história de usuário
- **THEN** a importação é rejeitada com a mensagem de que a história não foi encontrada
- **AND** a mensagem mostra um exemplo do formato aceito

### Requirement: Texto editado prevalece sobre o arquivo
Depois de importar um arquivo, o sistema SHALL enviar para geração o conteúdo atual dos campos, incluindo edições manuais feitas após a importação, e SHALL NOT reimportar o arquivo a cada interação.

#### Scenario: Edição após importação
- **WHEN** o usuário importa um arquivo e altera o critério 2 à mão
- **THEN** a geração usa o critério 2 alterado

### Requirement: Exemplos canônicos em 1 clique
A interface SHALL oferecer na barra lateral exemplos que preenchem os campos em 1 clique: Saque em Caixa Eletrônico, Cupom Promocional, Autenticação MFA, Login e Carrinho. Os campos preenchidos SHALL continuar editáveis, e nenhum exemplo SHALL disparar a geração sozinho.

#### Scenario: Carregar exemplo do Cupom
- **WHEN** o usuário escolhe "Cupom Promocional"
- **THEN** os campos são preenchidos com a história e os critérios do cupom
- **AND** nenhuma geração é disparada até o usuário enviar

#### Scenario: Exemplo usa o pipeline real
- **WHEN** o usuário carrega um exemplo e envia fora do modo demonstração
- **THEN** o resultado vem do provedor de LLM escolhido
