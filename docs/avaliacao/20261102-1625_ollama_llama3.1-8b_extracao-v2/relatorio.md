# Avaliação: ollama / llama3.1:8b / extracao-v2

- Conjunto: teste; casos: 7; rodadas por caso: 3; total de rodadas: 21
- Alinhamento semântico: não

## Total

| Métrica | Média ± desvio padrão |
|---|---|
| Validade | 0.29 ± 0.46 |
| Válido na 1ª tentativa | 0.14 ± 0.36 |
| Precisão de estados | 0.19 ± 0.36 |
| Recall de estados | 0.13 ± 0.24 |
| Precisão de transições | 0.00 ± 0.00 |
| Recall de transições | 0.00 ± 0.00 |
| Propriedades satisfeitas | 0.00 ± 0.00 |
| Timeout | 0.00 ± 0.00 |
| Duração (s) | 124.2 ± 46.7 |

Taxa de validade na primeira tentativa: 3/21 (14%).

## Por caso

| Caso | Conjunto | Validade | Precisão estados | Recall estados | Precisão transições | Recall transições | Propriedades | Duração (s) |
|---|---|---|---|---|---|---|---|---|
| chamado-suporte | teste | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 124.4 ± 2.7 |
| cupom-promocional | teste | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 180.7 ± 0.7 |
| emprestimo-biblioteca | teste | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 148.8 ± 2.2 |
| mfa-bloqueio | teste | 1.00 ± 0.00 | 0.33 ± 0.00 | 0.25 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 34.9 ± 1.2 |
| pagamento-boleto | teste | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 140.9 ± 1.3 |
| reserva-hotel | teste | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.67 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 85.0 ± 1.5 |
| saque-atm | teste | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 154.6 ± 2.6 |

## Propriedades que mais falharam

| Caso | Critério | Propriedade | Falhas | Motivo mais comum |
|---|---|---|---|---|
| mfa-bloqueio | 1 | Senha correta leva à etapa do código | 3 | estado não mapeado: AguardandoCodigo |
| mfa-bloqueio | 2 | Código correto libera o acesso | 3 | estado não mapeado: Autenticado |
| mfa-bloqueio | 3 | Um código incorreto permite nova tentativa | 3 | estado não mapeado: AguardandoCodigo |
| mfa-bloqueio | 3 | Depois de um erro, o código correto ainda autentica | 3 | estado não mapeado: Autenticado |
| mfa-bloqueio | 4 | Dois códigos incorretos ainda não bloqueiam | 3 | estado não mapeado: AguardandoCodigo |
| mfa-bloqueio | 4 | Três códigos incorretos seguidos bloqueiam | 3 | terminou em AcessoPendente, esperado AcessoBloqueado |
| reserva-hotel | 1 | Com quarto disponível a reserva fica pendente | 3 | evento não mapeado: selecionar_datas |
| reserva-hotel | 1 | Sem quarto disponível a reserva não é criada | 3 | evento não mapeado: selecionar_datas |
| reserva-hotel | 2 | Pagamento aprovado confirma a reserva | 3 | evento não mapeado: selecionar_datas |
| reserva-hotel | 3 | Fim do prazo expira a reserva pendente | 3 | evento não mapeado: selecionar_datas |
| reserva-hotel | 3 | Pagamento depois de expirar é recusado | 3 | evento não mapeado: selecionar_datas |
| reserva-hotel | 4 | Cancelar com 10 dias de antecedência é permitido | 3 | evento não mapeado: selecionar_datas |
| reserva-hotel | 4 | Cancelar com 3 dias de antecedência é recusado | 3 | evento não mapeado: selecionar_datas |

## Elementos não mapeados

Nomes do modelo extraído sem correspondência no gabarito. Revise se faltam sinônimos.

- mfa-bloqueio / estados: AcessoConcedido (3x), AcessoPendente (3x)
- mfa-bloqueio / variaveis: codigo_atual (3x)
- reserva-hotel / eventos: quarto_disponivel (3x), quarto_nao_disponivel (3x), pagamento_nao_aprovado (3x), cancelamento (3x)
- reserva-hotel / variaveis: horas_atestadas (3x), dias_antes_checkin (3x)

## Rodadas inválidas

- chamado-suporte #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '"AAAA-MM-DD"' de 'data_abertura' não é do tipo data.
- [esquema_invalido] variaveis.1: O valor_inicial '"AAAA-MM-DD"' de 'data_atual' não é do tipo data.
- chamado-suporte #2 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '"AAAA-MM-DD"' de 'data_abertura' não é do tipo data.
- [esquema_invalido] variaveis.1: O valor_inicial '"AAAA-MM-DD"' de 'data_atual' não é do tipo data.
- chamado-suporte #3 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '"AAAA-MM-DD"' de 'data_abertura' não é do tipo data.
- [esquema_invalido] variaveis.1: O valor_inicial '"AAAA-MM-DD"' de 'data_atual' não é do tipo data.
- cupom-promocional #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 8 erro(s):
- [guardas_sobrepostas] As guardas de T1 ('cupom_valido e data_atual <= validade') e T2 ('cupom_expirado') no par Carrinho / aplicar_cupom se sobrepõem: com cupom_expirado = True, cupom_valido = True, dat
- cupom-promocional #2 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 8 erro(s):
- [guardas_sobrepostas] As guardas de T1 ('cupom_valido e data_atual <= validade') e T2 ('cupom_expirado') no par Carrinho / aplicar_cupom se sobrepõem: com cupom_expirado = True, cupom_valido = True, dat
- cupom-promocional #3 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 8 erro(s):
- [guardas_sobrepostas] As guardas de T1 ('cupom_valido e data_atual <= validade') e T2 ('cupom_expirado') no par Carrinho / aplicar_cupom se sobrepõem: com cupom_expirado = True, cupom_valido = True, dat
- emprestimo-biblioteca #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 2 erro(s):
- [guardas_sobrepostas] As guardas de T1 ('livros_em_maos < 3 e não multa_pendente') e T5 ('livros_em_maos < 3') no par LivroDisponivel / pegar_livro se sobrepõem: com livros_em_maos = -1, multa_pendente 
- emprestimo-biblioteca #2 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 2 erro(s):
- [guardas_sobrepostas] As guardas de T1 ('livros_em_maos < 3 e não multa_pendente') e T5 ('livros_em_maos < 3') no par LivroDisponivel / pegar_livro se sobrepõem: com livros_em_maos = -1, multa_pendente 
- emprestimo-biblioteca #3 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 2 erro(s):
- [guardas_sobrepostas] As guardas de T1 ('livros_em_maos < 3 e não multa_pendente') e T5 ('livros_em_maos < 3') no par LivroDisponivel / pegar_livro se sobrepõem: com livros_em_maos = -1, multa_pendente 
- pagamento-boleto #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '0' de 'saldo' não é do tipo decimal.
- [esquema_invalido] variaveis.1: O valor_inicial '' de 'valor_boleto' não é do tipo decimal.
- [esquema_invalido] varia
- pagamento-boleto #2 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '0' de 'saldo' não é do tipo decimal.
- [esquema_invalido] variaveis.1: O valor_inicial '' de 'valor_boleto' não é do tipo decimal.
- [esquema_invalido] varia
- pagamento-boleto #3 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: Estrutura inválida:
- [esquema_invalido] variaveis.0: O valor_inicial '0' de 'saldo' não é do tipo decimal.
- [esquema_invalido] variaveis.1: O valor_inicial '' de 'valor_boleto' não é do tipo decimal.
- [esquema_invalido] varia
- saque-atm #1 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 5 erro(s):
- [guardas_sobrepostas] As guardas de T2 ('valor_saque <= saldo') e T6 ('valor_saque % 20 != 0') no par SaquePermitido / valor_saque se sobrepõem: com saldo = -0.01, valor_saque = -0.01 as duas são verdad
- saque-atm #2 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 5 erro(s):
- [guardas_sobrepostas] As guardas de T2 ('valor_saque <= saldo') e T6 ('valor_saque % 20 != 0') no par SaquePermitido / valor_saque se sobrepõem: com saldo = -0.01, valor_saque = -0.01 as duas são verdad
- saque-atm #3 (inválida): Não foi possível obter um modelo válido após 3 tentativas. Último erro: O modelo tem 5 erro(s):
- [guardas_sobrepostas] As guardas de T2 ('valor_saque <= saldo') e T6 ('valor_saque % 20 != 0') no par SaquePermitido / valor_saque se sobrepõem: com saldo = -0.01, valor_saque = -0.01 as duas são verdad
