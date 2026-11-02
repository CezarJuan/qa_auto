# Spec Delta

## Purpose

Oferecer sistemas sob teste conhecidos, corretos e com defeitos plantados, para medir se os testes gerados detectam falhas reais.

## ADDED Requirements

### Requirement: Implementação correta independente
Para Saque, Cupom, MFA e Carrinho, o projeto SHALL ter uma implementação correta escrita a partir da história e dos critérios, sem usar o modelo de estados nem o interpretador do gerador.

#### Scenario: Independência do modelo
- **WHEN** o código da implementação correta do Saque é inspecionado
- **THEN** ele não importa o modelo de estados nem o interpretador de guardas

### Requirement: Adaptador para cada sistema de referência
Cada sistema de referência SHALL ter um adaptador que cumpre a interface de adaptação gerada, traduzindo eventos e dados para as operações do sistema.

#### Scenario: Suíte do gabarito contra o sistema correto
- **WHEN** a suíte gerada do gabarito do Saque roda contra o Saque correto
- **THEN** todos os cenários passam

### Requirement: Mutantes documentados
Cada sistema de referência SHALL ter ao menos dois mutantes, cada um com uma única alteração, descrição do defeito e critério de aceite violado.

#### Scenario: Mutante do erro do explore no Saque
- **WHEN** os mutantes do Saque são listados
- **THEN** existe um mutante que retém o cartão no primeiro PIN inválido, associado ao critério 3

#### Scenario: Mutante do erro do explore no Carrinho
- **WHEN** os mutantes do Carrinho são listados
- **THEN** existe um mutante que permite finalizar com o carrinho vazio
