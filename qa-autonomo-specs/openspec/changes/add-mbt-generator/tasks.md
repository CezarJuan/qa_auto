# Tasks

## 1. Caminhos de teste

- [ ] 1.1 Implementar candidatos de valores e busca por configurações; teste: caminho para `CartaoRetido` tem 3 `pin_invalido`
- [ ] 1.2 Implementar a estratégia "todas as transições"; teste: 100% das transições cobertas nos gabaritos de Saque, Cupom e MFA
- [ ] 1.3 Implementar a estratégia "caminhos elementares" com limite; teste do aviso de limite atingido
- [ ] 1.4 Implementar cenários de borda; teste do saldo com valores 100 e 120
- [ ] 1.5 Implementar o relatório de cobertura com motivos; teste com transição além da profundidade máxima
- [ ] 1.6 Teste de determinismo: duas execuções produzem a mesma saída byte a byte

## 2. Gherkin

- [ ] 2.1 Adicionar `gherkin-official` e confirmar o parse de um `.feature` mínimo com `# language: pt`
- [ ] 2.2 Implementar o compilador com vocabulário fixo, nomes de cenário e tags; testes com snapshot do `.feature` do Saque
- [ ] 2.3 Validar todo `.feature` gerado com o parser nos testes dos 5 gabaritos

## 3. Pytest

- [ ] 3.1 Gerar `test_<slug>.py`, `adaptador_<slug>.py`, `conftest.py` e README; teste de nomes consistentes
- [ ] 3.2 Implementar o adaptador de simulação do modelo; os testes gerados dos 5 gabaritos passam contra ele
- [ ] 3.3 Teste: com o adaptador gerado sem alterações, todos os cenários falham com a mensagem explícita
- [ ] 3.4 Teste estático: o código gerado não contém `assert True` nem passos com corpo `pass`

## 4. Exportação e interface

- [ ] 4.1 Estender `/gerar` com caminhos, cobertura e artefatos; teste de contrato
- [ ] 4.2 Abas Gherkin, Pytest e Cobertura com conteúdo real e downloads; remover o aviso "em breve"; teste com AppTest
- [ ] 4.3 Gerar o zip; teste descompacta e roda `pytest --collect-only` sem erros
- [ ] 4.4 Implementar a geração por linha de comando; teste gera os 5 artefatos para o Saque
- [ ] 4.5 Opções de estratégia e de borda na interface e na linha de comando; teste sem `@borda`
- [ ] 4.6 Regravar os fixtures da demo com artefatos gerados

## 5. Integração

- [ ] 5.1 Rodar o fluxo completo (requisito → LLM → modelo → testes) para os 5 exemplos com Ollama e registrar cobertura e resultado em `docs/`

## Workflow follow-up

- Arquivar antes de `add-test-execution`.
