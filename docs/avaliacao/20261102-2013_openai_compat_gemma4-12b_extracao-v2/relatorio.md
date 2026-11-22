# Avaliação: openai_compat / gemma4:12b / extracao-v2

- Conjunto: desenvolvimento; casos: 8; rodadas por caso: 1; total de rodadas: 8
- Alinhamento semântico: não
- Extração determinística: não: o provedor não aceita temperatura e semente, então as rodadas medem variância

## Total

| Métrica | Média ± desvio padrão |
|---|---|
| Validade | 0.00 ± 0.00 |
| Válido na 1ª tentativa | 0.00 ± 0.00 |
| Precisão de estados | 0.00 ± 0.00 |
| Recall de estados | 0.00 ± 0.00 |
| Precisão de transições | 0.00 ± 0.00 |
| Recall de transições | 0.00 ± 0.00 |
| Propriedades satisfeitas | 0.00 ± 0.00 |
| Timeout | 1.00 ± 0.00 |
| Duração (s) | 362.2 ± 0.3 |

Taxa de validade na primeira tentativa: 0/8 (0%).

## Por caso

| Caso | Conjunto | Validade | Precisão estados | Recall estados | Precisão transições | Recall transições | Propriedades | Duração (s) |
|---|---|---|---|---|---|---|---|---|
| agendamento-consulta | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.1 ± 0.0 |
| assinatura-streaming | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.7 ± 0.0 |
| carrinho | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.1 ± 0.0 |
| login | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.7 ± 0.0 |
| matricula-curso | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.1 ± 0.0 |
| pedido-delivery | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.1 ± 0.0 |
| recuperacao-senha | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.1 ± 0.0 |
| transferencia-pix | desenvolvimento | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 362.1 ± 0.0 |

## Propriedades que mais falharam

Nenhuma propriedade falhou nas rodadas válidas.

## Elementos não mapeados

Nomes do modelo extraído sem correspondência no gabarito. Revise se faltam sinônimos.

Nenhum.

## Rodadas inválidas

- agendamento-consulta #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 168s.
- assinatura-streaming #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 178s.
- carrinho #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 177s.
- login #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 178s.
- matricula-curso #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 178s.
- pedido-delivery #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 178s.
- recuperacao-senha #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 178s.
- transferencia-pix #1 (timeout): O orçamento de 360s para a geração se esgotou após 2 tentativa(s). Último erro: OpenAI compatível: não respondeu em 178s.
