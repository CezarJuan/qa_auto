# Tasks

Comandos usam `py -m pytest`, pois o alias `python` está quebrado nesta máquina.

## 1. Sistemas exemplo

- [x] 1.1 Criar `sistemas_exemplo/base.py` e `__init__.py` com `Catalogo`, interface `estado`/`disparar`, registro `SISTEMAS` e `criar(id, variante)`; verificar em `tests/test_sistemas_exemplo.py` os erros de id, variante e evento fora do catálogo
- [x] 1.2 Implementar `sistemas_exemplo/login.py` com catálogo, regra de negócio, `LoginComBug`, requisitos numerados e modelo de referência; verificar por teste que a sequência de três senhas erradas bloqueia só na variante correta
- [x] 1.3 Implementar `sistemas_exemplo/saque.py` com catálogo, regra de negócio, `SaqueComBug`, requisitos numerados e modelo de referência; verificar por teste que o saque sem saldo entrega notas só na variante com bug
- [x] 1.4 Verificar por teste que o modelo de referência usa somente nomes do catálogo e cobre todos os critérios de cada exemplo

## 2. Modelo e validação

- [x] 2.1 Adicionar `finais` a `ModeloMBT` e `sistema` a `Requisicao`, com recusa de critérios sem numeração e de sistema desconhecido; verificar em `tests/test_validacao_modelo.py` e por `TestClient` que ambos retornam 422 sem chamar o LLM
- [x] 2.2 Estender `validar_coerencia` com nomes de estado seguros, ambiguidade, duplicatas, critério inexistente e finais desconhecidos; verificar com um teste por regra, incluindo aceitação de `ValidaçãoPIN`
- [x] 2.3 Adicionar a validação contra o catálogo; verificar por teste que nome fora do catálogo e estado inicial divergente falham indicando os valores
- [x] 2.4 Incluir o catálogo no prompt e conectá-lo em `gerar_modelo`; verificar com LLM falso que o prompt contém o catálogo e que o erro de catálogo volta na tentativa seguinte
- [x] 2.5 Exibir `finais` em `modelo_para_mermaid`; verificar por teste que o diagrama contém a saída para `[*]`
- [x] 2.6 Confirmar que os 12 testes de `tests/test_passo1.py` continuam passando com `py -m pytest tests`, ajustando apenas dados que violem as novas regras

## 3. Timeouts e configuração

- [x] 3.1 Ler `QA_TIMEOUT_LLM` em `backend/llm.py`, com padrão 180, e trocar o padrão de `OLLAMA_MODEL` para `llama3.1:8b` em `llm.py` e `.env.example`; verificar por teste os valores com e sem variável definida
- [x] 3.2 Fazer o front esperar `TIMEOUT_SEGUNDOS * MAX_TENTATIVAS` mais 10s; verificar por teste que o valor calculado supera o pior caso do backend
- [x] 3.3 Medir o fluxo real com Ollama, 3 rodadas de Login e de Saque; verificar registrando conclusão, duração e tentativas no `design.md`. Se o Login não concluir, reportar antes de seguir para o grupo 4

## 4. Geração de testes

- [x] 4.1 Implementar `gerar_caminhos` em `backend/geracao.py`; verificar em `tests/test_geracao.py` que todas as transições são cobertas, os caminhos partem do inicial e o resultado é estável entre execuções
- [x] 4.2 Implementar `gerar_feature`, com nomes únicos, critérios no título e eventos normalizados; verificar por teste os títulos com critérios, o caminho auxiliar e que um evento com aspas e quebra de linha não altera a estrutura
- [x] 4.3 Implementar `gerar_script`, com passos genéricos, `QA_VARIANTE`, cabeçalho com o comando de execução e versão esqueleto; verificar por teste que nenhum texto do modelo aparece no script
- [x] 4.4 Verificar de ponta a ponta, em diretório temporário, que os artefatos de cada referência passam na variante correta, falham na variante com bug e que o esqueleto falha com a mensagem de sistema não conectado

## 5. Execução e veredito

- [x] 5.1 Implementar `executar_testes` em `backend/execucao.py`, com subprocesso, JUnit XML, timeout de 60s e diretório temporário; verificar em `tests/test_execucao.py` o resultado por cenário e que o repositório fica sem resíduos
- [x] 5.2 Implementar o cálculo do veredito; verificar com um teste para cada linha da tabela do `design.md`
- [x] 5.3 Verificar de ponta a ponta os vereditos: referência dá "Bug detectado", modelo sem a transição do bug dá "Bug não detectado", modelo divergente dá "Modelo diverge do sistema", e script quebrado dá "Erro de execução"

## 6. Interface

- [x] 6.1 Remover `modelo`, `gherkin` e `pytest` de `demo_data.py`, ligando cada exemplo a um sistema; verificar que a suíte passa e não restam `assert True` nos dados da demo
- [x] 6.2 Adicionar o seletor de sistema e enviar `sistema` ao backend; verificar com `AppTest` que carregar um exemplo seleciona o sistema
- [x] 6.3 Gerar os artefatos com `backend.geracao` nos dois modos, com download pelos nomes corretos e aviso de esqueleto; verificar com `AppTest` em `tests/test_interface.py` no modo demo e no modo real com backend falso
- [x] 6.4 Adicionar o aviso de requisito editado na demonstração; verificar com `AppTest` que ele aparece só após editar
- [x] 6.5 Adicionar a ação de executar, o veredito e os resultados por cenário, descartando o resultado ao gerar novos artefatos; verificar com `AppTest` o veredito "Bug detectado" no Login e o descarte
- [x] 6.6 Atualizar `README.md` com status, seleção de sistema, execução, veredito, variáveis e exemplos reais; verificar seguindo os comandos documentados
- [x] 6.7 Conferir no navegador, com `streamlit run app.py`, geração, grafo com estado final, downloads e veredito de Login e Saque; verificar registrando o resultado na entrega

## 7. Validação final

- [x] 7.1 Rodar `py -m pytest tests` e `openspec validate gerar-testes-executaveis --strict`; verificar que ambos concluem sem erros e que `git status` não lista artefatos gerados pela execução

## Workflow follow-up

- Sincronizar as specs e arquivar a change depois da revisão.
