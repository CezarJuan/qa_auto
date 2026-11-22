# Proposal

## Why

A segunda metade do pipeline do 5W2H (modelo → caminhos → Gherkin → Pytest) não existe; o que aparece na tela é texto fixo. É aqui que está o núcleo de Model-Based Testing: os testes vêm de uma travessia determinística do modelo, com cobertura mensurável, e não de texto gerado pelo LLM. Sem isso, a tese do projeto ("o modelo formal elimina cenários alucinados") não pode ser demonstrada.

## What Changes

- Geração determinística de caminhos de teste sobre o modelo de estados, com duas estratégias: cobertura de todas as transições (padrão) e caminhos elementares por DFS, ambas respeitando guardas e contadores.
- Cenários de borda para guardas com comparação: valor na fronteira e logo fora dela.
- Relatório de cobertura de estados, transições e critérios de aceite, listando o que ficou sem cobertura e por quê.
- Compilação de cada caminho em um cenário Gherkin em português, com rastreabilidade por tags de critério.
- Geração de testes pytest-bdd com asserções reais sobre o sistema sob teste, por meio de uma interface de adaptação.
- Exportação dos artefatos pela interface (arquivos e pacote zip) e por linha de comando, que é o cenário mínimo (WCS) do 5W2H.
- **BREAKING** Remove o aviso "em breve" das abas Gherkin e Pytest.

## Capabilities

### New Capabilities
- `test-path-generation`: cálculo de caminhos de teste viáveis e da cobertura sobre o modelo de estados.
- `gherkin-generation`: compilação de caminhos em especificação BDD Gherkin.
- `pytest-generation`: geração de testes executáveis pytest-bdd e da interface de adaptação do sistema sob teste.
- `artifact-export`: exibição e exportação dos artefatos pela interface e pela linha de comando.

### Modified Capabilities
- `demo-mode`: remove o requisito que escondia os artefatos de teste fora da demo.

## Impact

- Novos módulos de caminhos, compilador Gherkin e gerador pytest no backend.
- `/gerar` passa a devolver caminhos, cobertura, `.feature` e `.py`.
- `app.py`: abas Gherkin, Pytest e Cobertura com conteúdo real.
- Novas dependências: `pytest-bdd` e `gherkin-official` (validação do Gherkin gerado).
