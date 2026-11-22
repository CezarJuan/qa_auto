# Tasks

## 1. Caminhos de teste

- [ ] 1.1 Implementar candidatos de valores e busca por configurações; teste: o caminho para `CartaoRetido` no gabarito `saque-atm` tem 3 `pin_invalido`
- [ ] 1.2 Implementar a estratégia "todas as transições" com término em estado final; teste: 100% das transições cobertas nos gabaritos de Saque ATM, Cupom e MFA e nos modelos de referência de Login e Saque
- [ ] 1.3 Implementar a estratégia "caminhos elementares" com limite; teste do aviso de limite atingido
- [ ] 1.4 Implementar os cenários de borda, com evento recusado quando aplicável; teste do saldo com valores 100 e 120
- [ ] 1.5 Implementar o relatório de cobertura com motivos; teste com transição além da profundidade máxima
- [ ] 1.6 Teste de determinismo: duas execuções produzem a mesma saída byte a byte

## 2. Gherkin

- [ ] 2.1 Adicionar `gherkin-official` e confirmar que ele e o `pytest-bdd` aceitam um `.feature` mínimo com `# language: pt`; registrar o resultado no design se houver desvio
- [ ] 2.2 Implementar o compilador com vocabulário fixo, nomes de cenário e tags; teste com snapshot do `.feature` do Saque ATM
- [ ] 2.3 Validar com o parser todo `.feature` gerado dos gabaritos e modelos de referência; teste parametrizado
- [ ] 2.4 Manter o texto do modelo apenas como dado; o teste existente de evento malicioso passa com o vocabulário novo

## 3. Pytest e sistemas exemplo

- [ ] 3.1 Estender `SistemaExemplo` com `definir_contexto`, `disparar(evento, dados) -> bool` e `estado_atual`; testes dos cenários da spec de `sistemas-exemplo`
- [ ] 3.2 Gerar `test_<slug>.py`, adaptador, `conftest.py` e `LEIAME.md`; teste de nomes consistentes
- [ ] 3.3 Implementar o adaptador de simulação do modelo; os testes gerados de todos os gabaritos passam contra ele
- [ ] 3.4 Teste: com o adaptador de esqueleto, todos os cenários falham com "Implemente o adaptador do sistema sob teste"
- [ ] 3.5 Teste estático: o código gerado não contém `assert True` nem passos com corpo `pass`; teste de recusa não confirmada
- [ ] 3.6 Adaptar `backend/execucao.py` ao pacote novo; o teste de ponta a ponta do veredito continua dando "Bug detectado" para Login e Saque

## 4. Exportação e interface

- [ ] 4.1 Abas Gherkin, Pytest e Cobertura com conteúdo gerado e downloads individuais; teste com `AppTest` nos modos real e demonstração
- [ ] 4.2 Gerar o zip; teste descompacta e roda `pytest --collect-only` sem erros
- [ ] 4.3 Implementar `python -m backend.cli gerar` com `--modelo` e `--requisito`; teste gera os artefatos do Saque ATM a partir do JSON e, com provedor fake, a partir do requisito
- [ ] 4.4 Opções de estratégia e de borda na interface e na linha de comando; teste sem `@borda`
- [ ] 4.5 Documentar a linha de comando e o pacote no README; conferir que o comando documentado funciona

## 5. Integração

- [ ] 5.1 Rodar o fluxo completo (requisito → LLM → modelo → testes → execução) para os 5 exemplos e registrar cobertura e resultado em `docs/medicoes/add-mbt-generator.md`

## Workflow follow-up

- Arquivar antes de `add-test-execution`.
