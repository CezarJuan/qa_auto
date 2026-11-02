# Spec Delta

## Purpose

Receber a história de usuário e os critérios de aceite em português, por formulário, arquivo ou exemplo canônico, e entregá-los normalizados ao pipeline de extração.

## ADDED Requirements

### Requirement: Campos da história de usuário
A interface SHALL oferecer campos para Papel, Ação e Benefício da história de usuário e uma área para os critérios de aceite, e SHALL rejeitar o envio quando a história estiver vazia, mostrando qual campo falta.

#### Scenario: Envio com história vazia
- **WHEN** o usuário envia o formulário sem preencher a Ação
- **THEN** o envio é bloqueado
- **AND** a interface informa que a Ação é obrigatória

#### Scenario: Envio completo
- **WHEN** o usuário preenche Papel, Ação, Benefício e ao menos um critério
- **THEN** o requisito é enviado para geração

### Requirement: Limite de tamanho da entrada
O sistema SHALL rejeitar entradas com mais de 2000 caracteres somando história e critérios, informando o tamanho atual e o limite.

#### Scenario: Entrada acima do limite
- **WHEN** a entrada tem 2100 caracteres
- **THEN** o envio é bloqueado com a mensagem de que o limite é 2000 e a entrada tem 2100

### Requirement: Numeração dos critérios de aceite
O sistema SHALL numerar os critérios de aceite de 1 a N na ordem em que aparecem, preservando a numeração do usuário quando ela já existir, e SHALL mostrar a lista numerada antes da geração.

#### Scenario: Critérios sem numeração
- **WHEN** o usuário digita três critérios em linhas separadas, sem números
- **THEN** o sistema os apresenta como critérios 1, 2 e 3

#### Scenario: Critérios já numerados
- **WHEN** o usuário digita "1. ...", "2. ..." e "3. ..."
- **THEN** o sistema mantém os números 1, 2 e 3

### Requirement: Importação de arquivo de requisitos
O sistema SHALL importar a história e os critérios de um arquivo de texto usando marcadores de seção explícitos, e SHALL NOT descartar linhas por conterem palavras comuns como "cada".

#### Scenario: Linha de critério com a palavra "cada"
- **WHEN** o arquivo tem o critério "cada tentativa inválida incrementa o contador"
- **THEN** a linha é importada como critério de aceite

#### Scenario: Arquivo sem história
- **WHEN** o arquivo não contém a seção da história de usuário
- **THEN** a importação é rejeitada com a mensagem de que a história não foi encontrada

### Requirement: Texto editado prevalece sobre o arquivo
Depois de importar um arquivo, o sistema SHALL enviar para geração o conteúdo atual dos campos, incluindo edições manuais feitas após a importação.

#### Scenario: Edição após importação
- **WHEN** o usuário importa um arquivo e altera o critério 2 à mão
- **THEN** a geração usa o critério 2 alterado

### Requirement: Exemplos canônicos em 1 clique
A interface SHALL oferecer, na barra lateral, exemplos que preenchem os campos em 1 clique: Saque em Caixa Eletrônico, Cupom Promocional, Autenticação MFA, Login e Carrinho. Os campos preenchidos SHALL continuar editáveis.

#### Scenario: Carregar exemplo do Saque
- **WHEN** o usuário clica em "Saque em Caixa Eletrônico"
- **THEN** os campos são preenchidos com a história e os critérios do saque
- **AND** nenhuma geração é disparada até o usuário enviar

#### Scenario: Exemplo usa o pipeline real
- **WHEN** o usuário carrega um exemplo e envia fora do modo demonstração
- **THEN** o resultado vem do provedor de LLM configurado
