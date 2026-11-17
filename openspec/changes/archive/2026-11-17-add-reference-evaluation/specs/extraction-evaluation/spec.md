# Spec Delta

## Purpose

Medir de forma reproduzível a qualidade da extração de modelos de estados para uma configuração de provedor, modelo e prompt, e comparar configurações entre si.

## ADDED Requirements

### Requirement: Execução por linha de comando
O executor SHALL rodar por linha de comando, recebendo provedor, modelo, número de rodadas por caso e conjunto (desenvolvimento, teste ou ambos), sem depender da interface web.

#### Scenario: Execução no conjunto de teste
- **WHEN** o usuário executa a avaliação com modelo `qwen2.5:7b`, 3 rodadas e conjunto teste
- **THEN** a extração é chamada 3 vezes para cada caso de teste
- **AND** os resultados são gravados em um diretório identificado por data e configuração

### Requirement: Alinhamento de nomes
Antes de comparar com o gabarito, o executor SHALL mapear estados, eventos e variáveis extraídos para os do gabarito por nome normalizado e sinônimos, e SHALL registrar os elementos não mapeados.

#### Scenario: Nome sinônimo
- **WHEN** o modelo extraído usa `UsuarioLogado` e o gabarito tem `Autenticado` com sinônimo `UsuarioLogado`
- **THEN** os dois estados são considerados o mesmo

### Requirement: Métricas por rodada
Para cada rodada, o executor SHALL registrar validade, número de tentativas, duração, timeout, precisão e recall de estados e de transições e a fração de propriedades satisfeitas.

#### Scenario: Rodada com estado extra
- **WHEN** o modelo extraído tem os 4 estados do gabarito e mais 1 inventado
- **THEN** o recall de estados é 1,0 e a precisão é 0,8

#### Scenario: Rodada com timeout
- **WHEN** a extração estoura o orçamento de tempo
- **THEN** a rodada conta como inválida e com timeout, e as métricas de qualidade ficam zeradas

### Requirement: Propriedades avaliadas por simulação
O executor SHALL verificar cada propriedade simulando o modelo extraído com os mesmos eventos e dados, e SHALL considerar falha quando algum evento ou variável da propriedade não puder ser mapeado.

#### Scenario: Evento não mapeado
- **WHEN** a propriedade usa `pin_invalido` e o modelo extraído não tem evento correspondente
- **THEN** a propriedade falha com motivo "evento não mapeado"

### Requirement: Relatório agregado
Ao final, o executor SHALL gerar um relatório com média e desvio padrão de cada métrica por caso e no total, taxa de validade na primeira tentativa e a lista das propriedades que mais falharam.

#### Scenario: Relatório gerado
- **WHEN** a avaliação termina
- **THEN** existem um arquivo de dados por rodada, um CSV resumo e um relatório em Markdown

### Requirement: Comparação entre configurações
O executor SHALL comparar duas ou mais execuções anteriores e mostrar, por métrica, o valor de cada configuração e a diferença.

#### Scenario: Comparar dois modelos
- **WHEN** o usuário compara a execução de `llama3.1:8b` com a de `qwen2.5:7b`
- **THEN** o relatório mostra lado a lado precisão, recall, propriedades, validade e latência
