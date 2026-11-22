# Avaliação: ollama / llama3.1:8b / extracao-v2

- Conjunto: desenvolvimento; casos: 8; rodadas por caso: 1; total de rodadas: 8
- Alinhamento semântico: não
- Extração determinística: sim (temperatura 0 e semente)

## Total

| Métrica | Média ± desvio padrão |
|---|---|
| Validade | 0.38 ± 0.52 |
| Válido na 1ª tentativa | 0.00 ± 0.00 |
| Precisão de estados | 0.31 ± 0.46 |
| Recall de estados | 0.30 ± 0.45 |
| Precisão de transições | 0.22 ± 0.41 |
| Recall de transições | 0.16 ± 0.29 |
| Propriedades satisfeitas | 0.15 ± 0.30 |
| Timeout | 0.00 ± 0.00 |
| Duração (s) | 129.3 ± 43.8 |

Taxa de validade na primeira tentativa: 0/8 (0%).

## Por caso

| Caso | Conjunto | Validade | Precisão estados | Recall estados | Precisão transições | Recall transições | Propriedades | Duração (s) |
|---|---|---|---|---|---|---|---|---|
| agendamento-consulta | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 113.7 ± 0.0 |
| assinatura-streaming | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 181.1 ± 0.0 |
| carrinho | desenvolvimento | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.75 ± 0.00 | 0.60 ± 0.00 | 0.40 ± 0.00 | 79.9 ± 0.0 |
| login | desenvolvimento | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.67 ± 0.00 | 0.80 ± 0.00 | 68.7 ± 0.0 |
| matricula-curso | desenvolvimento | 1.00 ± 0.00 | 0.50 ± 0.00 | 0.40 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 107.5 ± 0.0 |
| pedido-delivery | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 185.1 ± 0.0 |
| recuperacao-senha | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 150.9 ± 0.0 |
| transferencia-pix | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 147.5 ± 0.0 |

## Propriedades que mais falharam

| Caso | Critério | Propriedade | Falhas | Motivo mais comum |
|---|---|---|---|---|
| carrinho | 2 | Remover um de dois itens mantém o carrinho com itens | 1 | terminou em CarrinhoVazio, esperado CarrinhoComItens |
| carrinho | 3 | Finalizar com o carrinho vazio é recusado | 1 | o evento 'finalizar_compra' foi aceito, mas deveria ser recusado |
| carrinho | 4 | Finalizar com itens leva ao pagamento | 1 | terminou em CarrinhoComItens, esperado Pagamento |
| login | 1 | Senha correta depois de duas falhas ainda entra | 1 | terminou em DuasFalhas, esperado Dashboard |
| matricula-curso | 1 | Sem vagas a matrícula é recusada | 1 | evento não mapeado: matricular |
| matricula-curso | 1 | Com vagas a matrícula é feita | 1 | evento não mapeado: matricular |
| matricula-curso | 2 | Sem pagamento não é possível concluir o curso | 1 | evento não mapeado: matricular |
| matricula-curso | 3 | O pagamento libera o acesso às aulas | 1 | evento não mapeado: matricular |
| matricula-curso | 4 | Nota 7 aprova | 1 | evento não mapeado: matricular |
| matricula-curso | 4 | Nota 6,9 reprova | 1 | evento não mapeado: matricular |

## Elementos não mapeados

Nomes do modelo extraído sem correspondência no gabarito. Revise se faltam sinônimos.

- carrinho / variaveis: itens_no_carrinho (1x)
- matricula-curso / estados: TurmaVaga (1x), AulasDisponiveis (1x)
- matricula-curso / eventos: matricula_feita (1x), pagamento_feito (1x), curso_concluido (1x)

## Rodadas inválidas

- agendamento-consulta #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 1 erro(s):
- [guarda_invalida] Guarda de T3: Guarda com sintaxe inválida: 'data_atual - horario_agendado >= 1 dia'.
- assinatura-streaming #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 8 erro(s):
- [variavel_nao_declarada] A guarda de T4 usa a variável 'cobranca_falhou_3_veces', que não foi declarada.
- [variavel_nao_declarada] A guarda de T5 usa a variável 'cobranca_falhou_2_veces', que não foi d
- pedido-delivery #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 4 erro(s):
- [tipo_incompativel] Guarda de T3: Comparação entre tipos diferentes (booleano e texto).
- [tipo_incompativel] Guarda de T4: Comparação entre tipos diferentes (booleano e texto).
- [tipo_incompativel] Gu
- recuperacao-senha #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.1: O valor_inicial '0.0' de 'senha' não é do tipo decimal.
- transferencia-pix #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '0,00' de 'saldo' não é do tipo decimal.
- [esquema_invalido] variaveis.2: O valor_inicial '' de 'valor' não é do tipo decimal.
- [esquema_invalido] variaveis
