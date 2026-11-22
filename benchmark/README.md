# Casos de referência

Conjunto versionado de histórias de usuário com **modelo gabarito** e **propriedades comportamentais**, usado como verdade de referência para avaliar a extração (`python -m avaliacao`).

```bash
python -m avaliacao casos      # valida e lista os 15 casos
```

## Formato de um caso

Um arquivo `<id>.yaml` por caso. O `id` é igual ao nome do arquivo.

| Campo | Conteúdo |
|---|---|
| `id`, `dominio` | Identificador e domínio de negócio |
| `conjunto` | `desenvolvimento` (pode ser usado como exemplo de prompt e para ajustar) ou `teste` (nunca entra em prompt nem em treino) |
| `origem` | Opcional: `exemplo:<id>` (gabarito de `exemplos/`) ou `sistema:<id>` (modelo de referência de um sistema exemplo). Preenche `historia`, `criterios` e `gabarito`, para que cada modelo tenha uma única fonte |
| `sistema` | Opcional: id do sistema exemplo cujo catálogo vai no prompt |
| `historia`, `criterios` | Entrada da extração; critérios numerados |
| `gabarito` | Modelo de estados no formato `ModeloEstados` |
| `sinonimos` | Nomes alternativos aceitos para `estados`, `eventos` e `variaveis` do gabarito |
| `propriedades` | Ao menos uma por critério: `contexto` opcional, `eventos` (com `dados`), e `estado_esperado` e/ou `recusado: true` (o último evento deve ser recusado) |

O carregador recusa o caso se o gabarito não passar na validação, se algum critério ficar sem propriedade ou se o próprio gabarito não satisfizer alguma propriedade.

## Composição

| Conjunto | Casos |
|---|---|
| teste (7) | `saque-atm`, `cupom-promocional`, `mfa-bloqueio` (canônicos do 5W2H), `pagamento-boleto`, `reserva-hotel`, `emprestimo-biblioteca`, `chamado-suporte` |
| desenvolvimento (8) | `login` (exemplo resolvido do prompt), `carrinho`, `agendamento-consulta`, `assinatura-streaming`, `transferencia-pix`, `recuperacao-senha`, `pedido-delivery`, `matricula-curso` |

São 11 domínios: bancário, e-commerce, segurança, saúde, pagamentos, hotelaria, assinaturas, suporte, biblioteca, delivery e educação.

As propriedades `saque-atm` / "Um PIN errado não retém o cartão" e `carrinho` / "Finalizar com o carrinho vazio é recusado" reproduzem os erros semânticos encontrados no explore.

## Revisão em dupla do conjunto de teste

Os 10 casos novos (todos menos os 5 migrados de `exemplos/` e do Login) foram redigidos com apoio de LLM e **ainda precisam de revisão humana**. O conjunto de teste deve ser revisado pelos dois integrantes, cada um conferindo:

1. A história e os critérios estão em português claro e sem ambiguidade?
2. O gabarito representa exatamente os critérios, sem regra inventada nem faltando?
3. Cada propriedade testa o comportamento que o critério descreve, inclusive fronteiras (ex.: 30 dias, 100 reais)?
4. Os sinônimos cobrem nomes razoáveis que um LLM usaria?

Registre aqui o resultado (data, quem revisou e o que mudou):

| Caso (teste) | Revisor 1 | Revisor 2 | Data | Ajustes |
|---|---|---|---|---|
| saque-atm | | | | |
| cupom-promocional | | | | |
| mfa-bloqueio | | | | |
| pagamento-boleto | | | | |
| reserva-hotel | | | | |
| emprestimo-biblioteca | | | | |
| chamado-suporte | | | | |

Depois de qualquer ajuste, rode `python -m avaliacao casos` e `python -m pytest tests/test_avaliacao.py`.
