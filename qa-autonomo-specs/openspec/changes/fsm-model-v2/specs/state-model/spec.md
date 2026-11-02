# Spec Delta

## Purpose

Definir o formato do modelo de estados finito estendido que representa as regras de negócio de uma história de usuário e serve de base para gerar caminhos e testes.

## ADDED Requirements

### Requirement: Estados com identificador, rótulo e tipo
Cada estado SHALL ter um identificador em PascalCase ASCII (`^[A-Z][A-Za-z0-9]*$`), um rótulo livre em português e um tipo: inicial, intermediário ou final.

#### Scenario: Estado com rótulo acentuado
- **WHEN** o modelo descreve o estado "Cartão retido"
- **THEN** o estado tem id "CartaoRetido", rótulo "Cartão retido" e tipo final

#### Scenario: Id inválido
- **WHEN** um estado tem id "Com itens"
- **THEN** o modelo não está no formato válido

### Requirement: Variáveis do modelo
O modelo SHALL declarar variáveis com nome em snake_case, tipo (inteiro, decimal, booleano ou data) e categoria: de estado, com valor inicial e alterável por ações; de entrada, informada quando o evento ocorre; ou de contexto, definida no início do cenário e constante.

#### Scenario: Contador de tentativas
- **WHEN** a história diz que o cartão é retido após 3 PINs inválidos
- **THEN** o modelo declara a variável de estado `tentativas`, inteiro, valor inicial 0

#### Scenario: Valor informado no evento
- **WHEN** a história diz que o cliente informa o valor do saque
- **THEN** o modelo declara a variável de entrada `valor`, decimal

#### Scenario: Saldo da conta
- **WHEN** a história diz que o saque só ocorre se houver saldo suficiente
- **THEN** o modelo declara a variável de contexto `saldo`, decimal

### Requirement: Transições com evento, guarda, ações e critérios
Cada transição SHALL ter id, estado de origem, evento, estado de destino, guarda opcional, lista de ações e lista dos números dos critérios de aceite que ela representa.

#### Scenario: Transição com guarda e ação
- **WHEN** um PIN inválido com menos de 2 erros anteriores é informado
- **THEN** existe uma transição de `AguardandoPin` para `AguardandoPin` com evento `pin_invalido`, guarda `tentativas < 2`, ação `tentativas += 1` e critério 3

### Requirement: Linguagem de guardas
Guardas SHALL usar apenas variáveis declaradas, literais, aritmética `+ - %`, comparações `== != < <= > >=` e os operadores `e`, `ou`, `não`, com parênteses.

#### Scenario: Guarda válida
- **WHEN** a guarda é `valor <= saldo e valor > 0`
- **THEN** a guarda está no formato válido

#### Scenario: Valor múltiplo das cédulas
- **WHEN** a guarda é `valor % 20 == 0`
- **THEN** a guarda está no formato válido

#### Scenario: Guarda com chamada de função
- **WHEN** a guarda é `validar(valor)`
- **THEN** a guarda não está no formato válido

### Requirement: Linguagem de ações
Ações SHALL ser atribuições a variáveis de estado nas formas `x = expr`, `x += expr` ou `x -= expr`, onde `expr` segue a linguagem de guardas, e SHALL ser executadas na ordem declarada após a transição ser escolhida.

#### Scenario: Ação sobre variável de entrada
- **WHEN** uma ação é `valor = 0` e `valor` é variável de entrada
- **THEN** a ação não está no formato válido

#### Scenario: Ação sobre variável de contexto
- **WHEN** uma ação é `saldo -= valor` e `saldo` é variável de contexto
- **THEN** a ação não está no formato válido

### Requirement: Análise antes do modelo
O modelo SHALL incluir um campo de análise em texto, preenchido antes dos estados, que liste as regras identificadas em cada critério de aceite.

#### Scenario: Análise presente
- **WHEN** um modelo é produzido para 3 critérios
- **THEN** o campo de análise cita os critérios 1, 2 e 3
