# Spec Delta

## Purpose

Exibir os artefatos gerados na interface e permitir exportá-los, por download ou por linha de comando, num formato pronto para executar.

## ADDED Requirements

### Requirement: Abas de resultado com conteúdo gerado
Após uma geração, a interface SHALL mostrar em abas o diagrama, o Gherkin, o teste pytest e o relatório de cobertura, todos produzidos para o requisito enviado.

#### Scenario: Aba Gherkin
- **WHEN** a geração do Cupom termina
- **THEN** a aba Gherkin mostra o `.feature` do Cupom com um cenário por caminho

### Requirement: Download individual e em pacote
A interface SHALL oferecer download de cada artefato (modelo em JSON, diagrama `.mmd`, `.feature`, teste `.py`, adaptador) e de um pacote zip com todos eles e instruções de execução.

#### Scenario: Pacote executável
- **WHEN** o usuário baixa o zip, descompacta e roda `pytest` na pasta
- **THEN** o pytest coleta todos os cenários sem erro de coleta

### Requirement: Geração por linha de comando
O sistema SHALL gerar os mesmos artefatos por linha de comando, a partir de um arquivo de requisito e de um diretório de saída, sem interface web.

#### Scenario: Cenário mínimo sem interface
- **WHEN** o usuário executa a geração por linha de comando com o arquivo do Saque
- **THEN** o diretório de saída contém o modelo JSON, o `.mmd`, o `.feature`, o teste e o adaptador

### Requirement: Escolha da estratégia
A interface e a linha de comando SHALL permitir escolher a estratégia de caminhos e ativar ou desativar os cenários de borda.

#### Scenario: Sem cenários de borda
- **WHEN** o usuário desativa os cenários de borda
- **THEN** nenhum cenário do `.feature` tem a tag `@borda`
