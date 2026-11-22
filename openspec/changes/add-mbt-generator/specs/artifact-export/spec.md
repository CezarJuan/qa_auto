# Spec Delta

## Purpose

Exibir os artefatos gerados na interface e permitir exportá-los, por download ou por linha de comando, num formato pronto para executar.

## ADDED Requirements

### Requirement: Abas de resultado com conteúdo gerado
Após uma geração, no modo real ou na demonstração, a interface SHALL mostrar em abas o diagrama, o Gherkin, o teste pytest e o relatório de cobertura, todos produzidos pelo gerador a partir do modelo exibido, e nenhum vindo de texto fixo.

#### Scenario: Aba Gherkin no modo real
- **WHEN** a geração do Cupom termina
- **THEN** a aba Gherkin mostra o `.feature` do Cupom com um cenário por caminho

#### Scenario: Modo demonstração
- **WHEN** a pessoa gera um exemplo no modo demonstração
- **THEN** os artefatos são gerados do modelo de referência, sem backend e sem LLM

### Requirement: Download individual e em pacote
A interface SHALL oferecer download de cada artefato (modelo em JSON, diagrama `.mmd`, `.feature`, teste `.py` e adaptador) e de um pacote zip com todos eles, o `conftest.py` e instruções de execução.

#### Scenario: Pacote executável
- **WHEN** o usuário baixa o zip, descompacta na raiz do projeto e roda `pytest` na pasta
- **THEN** o pytest coleta todos os cenários sem erro de coleta

### Requirement: Geração por linha de comando
O sistema SHALL gerar os mesmos artefatos por linha de comando, a partir de um arquivo de requisito ou de um modelo JSON e de um diretório de saída, sem interface web.

#### Scenario: Cenário mínimo a partir do modelo
- **WHEN** o usuário executa a geração por linha de comando com o gabarito do Saque ATM em JSON
- **THEN** o diretório de saída contém o modelo JSON, o `.mmd`, o `.feature`, o teste, o adaptador e o `conftest.py`, sem chamar o LLM

#### Scenario: A partir do requisito
- **WHEN** o usuário executa a geração com um arquivo no formato `# História` / `# Critérios` e um provedor
- **THEN** o modelo é extraído pelo provedor e os mesmos artefatos são gravados

### Requirement: Escolha da estratégia
A interface e a linha de comando SHALL permitir escolher a estratégia de caminhos e ativar ou desativar os cenários de borda.

#### Scenario: Sem cenários de borda
- **WHEN** o usuário desativa os cenários de borda
- **THEN** nenhum cenário do `.feature` tem a tag `@borda`
