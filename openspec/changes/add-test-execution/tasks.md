# Tasks

## 1. Suíte manual (fazer primeiro, antes de ver as suítes geradas)

- [ ] 1.1 Escrever à mão os `.feature` de Saque ATM, Cupom e MFA com o vocabulário fixo, cronometrando; registrar em `suite_manual/<slug>/metadados.yaml` e conferir que o parser Gherkin aceita cada arquivo

## 2. Sistemas exemplo

- [ ] 2.1 Implementar Saque ATM, Cupom, MFA e Carrinho corretos, com catálogo, requisitos e o gabarito de `exemplos/` como modelo de referência; teste estático garante que nenhum importa o modelo nem `backend/expressoes.py`
- [ ] 2.2 Remover o Saque antigo e atualizar exemplos, demonstração e testes para `saque-atm`; a suíte de testes inteira passa
- [ ] 2.3 Verificar que a suíte gerada do modelo de referência passa 100% na variante correta de cada sistema; teste parametrizado
- [ ] 2.4 Escrever ao menos 2 mutantes por sistema, incluindo os erros do explore e um de fronteira por sistema, com `mutantes.yaml`; teste confere que cada mutante sobrescreve um único método e tem descrição e critério
- [ ] 2.5 Aceitar `correto`, id de mutante e o alias `bug` em `criar`; testes dos cenários da spec de seleção de variante

## 3. Execução e relatório

- [ ] 3.1 Executar contra a variante correta e cada mutante, em subprocesso e com tempo limite; teste com suíte que dorme além do limite
- [ ] 3.2 Agregar resultados por cenário e por critério via tags; teste com duas falhas em `@CA-3`
- [ ] 3.3 Calcular o veredito pela tabela do design, com sobreviventes e falsos alarmes; um teste por linha da tabela
- [ ] 3.4 Detectar falsos alarmes com o modelo errado do Saque registrado no explore; teste de ponta a ponta
- [ ] 3.5 Implementar a comparação com a suíte manual; teste do relatório comparativo do MFA

## 4. Interface e linha de comando

- [ ] 4.1 Aba de execução com taxa de detecção, sobreviventes, falsos alarmes e resultado por critério; teste com `AppTest`
- [ ] 4.2 Mensagem para requisitos sem sistema exemplo apontando para o adaptador; teste com requisito de boleto
- [ ] 4.3 Comandos `executar` e `comparar` na linha de comando, documentados no README; teste roda a análise do Saque ATM

## 5. Resultados para o relatório da disciplina

- [ ] 5.1 Gerar e salvar em `docs/resultados/` a tabela final (mutantes detectados, bordas, tempo e falsos alarmes) para os 3 exemplos canônicos, com a suíte do modelo de referência e a do modelo extraído

## Workflow follow-up

- Arquivar antes de `add-persistence`.
