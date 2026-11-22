# Spec Delta

## MODIFIED Requirements

### Requirement: Sistemas exemplo disponíveis
O projeto MUST oferecer os sistemas exemplo Login, Saque ATM, Cupom Promocional, Autenticação MFA e Carrinho, cada um identificado por um id estável.

#### Scenario: Listar sistemas
- **WHEN** o catálogo de sistemas exemplo é consultado
- **THEN** ele contém os ids `login`, `saque-atm`, `cupom-promocional`, `mfa-bloqueio` e `carrinho`, cada um com um nome de exibição

### Requirement: Comportamento implementado como regra de negócio
Os sistemas exemplo MUST implementar o comportamento com regras de negócio próprias, escritas a partir da história e dos critérios, e MUST NOT usar o modelo de referência nem o interpretador de guardas e ações.

#### Scenario: Independência do modelo
- **WHEN** o modelo de referência de um sistema é alterado
- **THEN** o comportamento do sistema permanece o mesmo

#### Scenario: Sem importação do modelo
- **WHEN** o código da variante correta do Saque ATM é inspecionado
- **THEN** ele não importa o modelo de estados nem o interpretador de guardas

### Requirement: Variantes correta e com bug
Cada sistema exemplo MUST oferecer uma variante correta e ao menos dois mutantes. Cada mutante MUST diferir da correta por uma única alteração e declarar a descrição do defeito e o critério de aceite violado. Ao menos um mutante por sistema MUST alterar uma fronteira.

#### Scenario: Selecionar variante
- **WHEN** um sistema é criado informando a variante correta ou o id de um mutante
- **THEN** é retornada uma instância nova da variante pedida, no estado inicial

#### Scenario: Variante inexistente
- **WHEN** um sistema é criado com id ou variante desconhecidos
- **THEN** é lançado um erro que identifica o valor inválido

#### Scenario: Mutante do erro do explore no Saque ATM
- **WHEN** os mutantes do Saque ATM são listados
- **THEN** existe um mutante que retém o cartão no primeiro PIN inválido, associado ao critério 3

#### Scenario: Mutante do erro do explore no Carrinho
- **WHEN** os mutantes do Carrinho são listados
- **THEN** existe um mutante que permite finalizar com o carrinho vazio

### Requirement: Modelo de referência
Cada sistema exemplo MUST incluir um modelo de referência no formato do modelo de estados que passa na validação, descreve corretamente a variante correta e usa somente nomes do catálogo.

#### Scenario: Referência válida e fiel
- **WHEN** testes são gerados a partir do modelo de referência e executados contra a variante correta
- **THEN** todos os cenários passam

#### Scenario: Referência passa na validação
- **WHEN** o modelo de referência é validado com os critérios do exemplo e o catálogo
- **THEN** a validação não devolve erros
