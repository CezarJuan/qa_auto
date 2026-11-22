# Tasks

## 1. Casos de referência

- [x] 1.1 Definir o esquema do caso (YAML) e o carregador com validação: gabarito válido e propriedade para cada critério; testes com caso completo e caso sem propriedade
- [x] 1.2 Migrar os gabaritos de `exemplos/` (`saque-atm`, `cupom-promocional`, `mfa-bloqueio`, `carrinho`) e o modelo de referência do Login para `benchmark/`, com propriedades, incluindo as que reproduzem os erros do explore; o carregador aceita os 5 casos
- [x] 1.3 Escrever mais 10 casos em pelo menos 3 novos domínios (por exemplo: agendamento, boleto, reserva, assinatura, chamado de suporte); o carregador aceita os 15
- [ ] 1.4 Revisar em dupla o conjunto de teste e registrar a revisão em `benchmark/README.md`

## 2. Simulação e alinhamento

- [x] 2.1 Implementar o simulador de propriedades (eventos, dados, evento recusado) reusando o interpretador; testes com as duas propriedades do Saque contra o gabarito e contra o modelo errado do explore
- [x] 2.2 Implementar alinhamento por normalização e sinônimos; teste `UsuarioLogado` → `Autenticado`
- [x] 2.3 Implementar alinhamento semântico opcional; teste com embeddings fake

## 3. Métricas e executor

- [x] 3.1 Calcular precisão e recall de estados e transições; teste do cenário 4 + 1 estado extra (0,8 / 1,0)
- [x] 3.2 Implementar o executor por linha de comando com provedor, modelo, rodadas, conjunto e `--casos`; teste com provedor fake
- [x] 3.3 Recusar configurações com caso de teste vazado nos exemplos do prompt; teste com `mfa-bloqueio` vazado
- [x] 3.4 Gerar `rodadas/*.json`, `resumo.csv` e `relatorio.md`; teste confere colunas e seções
- [x] 3.5 Implementar o subcomando `comparar`; teste com duas execuções fake

## 4. Linha de base

- [x] 4.1 Rodar a avaliação com `llama3.1:8b` (prompt `extracao-v2`, 3 rodadas, conjunto teste) e salvar como linha de base em `docs/avaliacao/`; se o Ollama não rodar na máquina disponível, usar o Gemini e registrar o motivo no relatório
- [x] 4.2 Documentar em `docs/avaliacao/README.md` como rodar e comparar avaliações

## Workflow follow-up

- Abrir o change de melhoria do modelo do Ollama usando esta linha de base como ponto de comparação.
