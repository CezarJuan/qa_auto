# Tasks

## 1. Formato do modelo

- [ ] 1.1 Implementar o esquema Pydantic (`Variavel`, `Estado`, `Transicao`, `ModeloEstados`) com `analise` como primeiro campo; testes de formato com ids válidos e inválidos
- [ ] 1.2 Implementar parser e interpretador de guardas e ações com lista de nós permitidos; testes para guarda válida, chamada de função rejeitada e ação sobre variável de entrada rejeitada
- [ ] 1.3 Escrever os gabaritos manuais de Login, Saque ATM, Cupom, MFA e Carrinho no formato novo em `exemplos/`; cada um passa no esquema

## 2. Validação

- [ ] 2.1 Validar estado inicial único, finais sem saída e ao menos um final; testes dos cenários da spec
- [ ] 2.2 Validar alcançabilidade e término com o grafo; testes de inalcançável e beco sem saída
- [ ] 2.3 Validar referências a estados e variáveis e compatibilidade de tipos; teste com `saldo` não declarado
- [ ] 2.4 Validar critérios inexistentes e não cobertos (corrige bug 10); testes com critério 99 e critério 2 ausente
- [ ] 2.5 Validar determinismo por valores de fronteira e transições duplicadas; testes com guardas sobrepostas (`tentativas = 2`) e complementares
- [ ] 2.6 Padronizar erros com código, elementos e mensagem, devolvendo todos de uma vez; teste com dois erros simultâneos
- [ ] 2.7 Confirmar que os 5 gabaritos passam na validação sem erros

## 3. Extração

- [ ] 3.1 Enviar o JSON Schema no `format` do Ollama com temperatura 0 e semente; teste com fake verifica os parâmetros enviados
- [ ] 3.2 Reescrever o prompt com critérios numerados, linguagens de guarda e ação e o exemplo resolvido de Login; versionar como `prompts/extracao_v2.md`
- [ ] 3.3 Adaptar o retry para enviar erros agrupados e o modelo anterior; teste com fake que erra na 1ª e acerta na 2ª
- [ ] 3.4 Incluir no resultado as tentativas (duração, resultado, erros) e a versão do prompt, provedor e modelo; teste de contrato do `/gerar`

## 4. Interface e diagrama

- [ ] 4.1 Mostrar guardas nos rótulos e ligar estados finais ao marcador de fim; validar com `mmdc`
- [ ] 4.2 Exibir variáveis, análise e tentativas na interface; teste com AppTest
- [ ] 4.3 Regravar os fixtures da demo no formato novo; teste da demo continua passando

## 5. Integração

- [ ] 5.1 Rodar os 5 exemplos no fluxo real com Ollama e registrar em `docs/` quantos passam na validação e em quantas tentativas

## Workflow follow-up

- Arquivar este change antes de iniciar `add-reference-evaluation` e `add-mbt-generator`.
