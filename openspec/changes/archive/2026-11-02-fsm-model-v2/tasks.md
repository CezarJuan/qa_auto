# Tasks

## 1. Formato do modelo

- [x] 1.1 Implementar `Variavel`, `Estado`, `Transicao` e `ModeloEstados` com `analise` como primeiro campo e remover `ModeloMBT`; testes de formato com ids e eventos válidos e inválidos e variável de estado sem valor inicial
- [x] 1.2 Implementar o parser e o interpretador de guardas e ações em `backend/expressoes.py`; testes para guarda válida, `%`, chamada de função rejeitada, ação sobre variável de entrada e de contexto rejeitada
- [x] 1.3 Migrar os catálogos e modelos de referência de Login e Saque para o formato novo, com eventos em snake_case e sem o laço no final do Login; testes de `sistemas_exemplo` continuam passando
- [x] 1.4 Escrever os gabaritos de `cupom-promocional`, `mfa-bloqueio`, `carrinho` e `saque-atm` em `exemplos/`; cada um passa no esquema

## 2. Validação

- [x] 2.1 Validar inicial único, ao menos um final e finais sem saída; testes dos cenários da spec
- [x] 2.2 Validar alcançabilidade e término; testes de estado inalcançável e beco sem saída
- [x] 2.3 Validar referências a estados e variáveis e compatibilidade de tipos; teste com `saldo` não declarado e destino inexistente
- [x] 2.4 Validar critérios inexistentes e não cobertos; testes com critério 99 e critério 2 ausente
- [x] 2.5 Validar determinismo por valores de fronteira e transições duplicadas; testes com guardas sobrepostas, complementares e sem guarda
- [x] 2.6 Validar conformidade com o catálogo, inclusive variáveis; testes com variável fora do catálogo e inicial divergente
- [x] 2.7 Padronizar `ErroValidacao` com código, elementos e mensagem, ordenados por grupo; teste com dois erros simultâneos
- [x] 2.8 Confirmar que os modelos de referência e os 4 gabaritos passam na validação; teste parametrizado

## 3. Extração

- [x] 3.1 Enviar o JSON Schema com temperatura 0 e semente `QA_SEMENTE` ao Ollama, e esquema com temperatura 0 ao Gemini; teste com fake verifica os parâmetros
- [x] 3.2 Escrever `backend/prompts/extracao_v2.md` com critérios numerados, linguagens de guarda e ação, seção de catálogo com variáveis e o exemplo resolvido do Login; teste confere as seções do prompt montado
- [x] 3.3 Adaptar o retry para reenviar o modelo anterior e os erros agrupados; teste com fake que erra na 1ª tentativa e acerta na 2ª
- [x] 3.4 Incluir no resultado e em `/gerar` a versão do prompt, o provedor e o modelo (o histórico de tentativas já existe); teste de contrato do `/gerar`, inclusive o 422 com os erros da última tentativa

## 4. Pipeline, interface e diagrama

- [x] 4.1 Adaptar `backend/geracao.py` ao formato novo (ids, tipo, `criterios`), mantendo a BFS; testes de geração e de execução existentes passam com os modelos migrados
- [x] 4.2 Diagrama com `state "rótulo" as Id`, guardas nos rótulos e finais ligados ao marcador de fim; testes estruturais dos cenários da spec
- [x] 4.3 Exibir análise, variáveis e tentativas na interface; teste com `AppTest`
- [x] 4.4 Ligar os exemplos Cupom, MFA e Carrinho aos gabaritos na demonstração; teste com `AppTest` do Cupom no modo demo

## 5. Integração

- [x] 5.1 Rodar os 5 exemplos no fluxo real e registrar em `docs/medicoes/fsm-model-v2.md` quantos passam na validação e em quantas tentativas

## Workflow follow-up

- Arquivar este change antes de iniciar `add-reference-evaluation` e `add-mbt-generator`.
