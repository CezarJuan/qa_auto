# Tasks

## 1. Suíte manual (fazer primeiro, antes de ver as suítes geradas)

- [ ] 1.1 Escrever à mão os `.feature` de Saque, Cupom e MFA com o vocabulário fixo, cronometrando; registrar em `suite_manual/<slug>/metadados.yaml`

## 2. Sistemas de referência

- [ ] 2.1 Implementar Saque, Cupom, MFA e Carrinho corretos sem importar o modelo; teste estático de imports
- [ ] 2.2 Implementar os adaptadores; a suíte gerada do gabarito passa 100% em cada sistema correto
- [ ] 2.3 Escrever ao menos 2 mutantes por sistema, incluindo os dois erros do explore e um de fronteira por sistema; `mutantes.yaml` com descrição e critério
- [ ] 2.4 Teste: cada mutante difere do correto em uma única alteração (diff revisado e anotado no `mutantes.yaml`)

## 3. Execução e relatório

- [ ] 3.1 Implementar a execução em subprocesso com JUnit XML e tempo limite; teste com suíte que dorme além do limite
- [ ] 3.2 Agregar resultados por cenário e por critério via tags; teste com duas falhas em `@CA-3`
- [ ] 3.3 Implementar a análise de mutantes com sobreviventes; teste com mutante que nenhuma suíte detecta
- [ ] 3.4 Implementar a detecção de falsos alarmes; teste com o modelo errado do Saque registrado no explore
- [ ] 3.5 Implementar a comparação com a suíte manual; teste do relatório comparativo do MFA

## 4. Interface e linha de comando

- [ ] 4.1 Aba "Execução" com escolha correto/mutante, resultados e análise de mutantes; teste com AppTest
- [ ] 4.2 Mensagem para histórias sem sistema de referência; teste com requisito de boleto
- [ ] 4.3 Comando de execução e de análise de mutantes; documentar no README

## 5. Resultados para o relatório da disciplina

- [ ] 5.1 Gerar e salvar em `docs/resultados/` a tabela final: mutantes detectados, bordas, tempo e falsos alarmes para os 3 exemplos canônicos, com suíte do gabarito e suíte do modelo extraído

## Workflow follow-up

- Arquivar antes de `add-persistence`.
