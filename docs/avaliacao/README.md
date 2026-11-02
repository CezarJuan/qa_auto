# Avaliação da extração

Mede, de forma reproduzível, a qualidade dos modelos de estados extraídos por uma configuração (provedor, modelo e versão do prompt) contra os casos de referência de `benchmark/`, e compara configurações entre si. A interface e a API não são usadas.

## Rodar uma avaliação

```bash
# Linha de base: 3 rodadas por caso de teste com o Ollama
python -m avaliacao executar --provedor ollama --modelo llama3.1:8b --rodadas 3 --conjunto teste

# Outro modelo, só em dois casos (útil em hardware modesto)
python -m avaliacao executar --provedor ollama --modelo qwen2.5:7b --casos saque-atm,mfa-bloqueio

# Gemini (precisa de GEMINI_API_KEY no .env)
python -m avaliacao executar --provedor gemini --modelo gemini-3.8-flash --rodadas 3
```

| Opção | Padrão | Uso |
|---|---|---|
| `--provedor` | — | `ollama` ou `gemini` |
| `--modelo` | — | Nome do modelo no provedor |
| `--rodadas` | 3 | Extrações por caso (para estimar a variância) |
| `--conjunto` | `teste` | `teste`, `desenvolvimento` ou `ambos` |
| `--casos` | todos | Ids separados por vírgula |
| `--saida` | `resultados/` | Pasta base dos resultados |
| `--alinhamento-semantico` | desligado | Usa embeddings (`nomic-embed-text` no Ollama) para casar nomes sem sinônimo; deixa as métricas não determinísticas |

Antes de começar, o executor mostra o número de extrações e uma estimativa de duração. Ele também **recusa** a configuração se o prompt usar como exemplo um caso do conjunto de teste, seja declarado em `EXEMPLOS_DO_PROMPT` (`backend/prompts/__init__.py`), seja com o texto de uma história ou de um critério de teste copiado no prompt.

Cada execução gera `resultados/<AAAAMMDD-HHMM>_<provedor>_<modelo>_<prompt>/` com:

- `config.json`: configuração e casos avaliados;
- `rodadas/<caso>_<n>.json`: métricas, propriedades, nomes não mapeados, tentativas e o modelo extraído;
- `resumo.csv`: uma linha por rodada;
- `relatorio.md`: média e desvio padrão por métrica (total e por caso), validade na 1ª tentativa, propriedades que mais falharam, nomes não mapeados e rodadas inválidas.

## Comparar configurações

```bash
python -m avaliacao comparar resultados/<execucao-a> resultados/<execucao-b> --saida comparacao.md
```

A tabela mostra, por métrica, a média de cada execução e a diferença em relação à primeira.

## Métricas

| Métrica | Como é calculada |
|---|---|
| Validade | Rodada em que a extração produziu um modelo que passou na validação (dentro de 3 tentativas e do orçamento) |
| Válido na 1ª tentativa | Válido sem precisar de correção |
| Precisão / recall de estados | Estados extraídos que casam com o gabarito ÷ estados extraídos / ÷ estados do gabarito |
| Precisão / recall de transições | Igual, com a tripla (origem, evento, destino). A guarda não entra: ela é avaliada pelas propriedades, o que evita penalizar `valor <= saldo` vs `saldo >= valor` |
| Propriedades satisfeitas | Fração das propriedades do caso que valem ao simular o modelo extraído com os mesmos eventos e dados. Evento, variável ou estado sem correspondência faz a propriedade falhar |
| Timeout / duração | Rodada que esgotou o orçamento de tempo; duração total da extração |

Rodadas inválidas e com timeout entram com métricas de qualidade zeradas.

Os nomes são casados por normalização (minúsculas, sem acento, sem `_`, espaço ou hífen), pelo rótulo do estado e pelos sinônimos do caso. Os que sobram aparecem no relatório, em "Elementos não mapeados", para revisão dos sinônimos.

## Linha de base

A linha de base está em [`20261102-1625_ollama_llama3.1-8b_extracao-v2/`](20261102-1625_ollama_llama3.1-8b_extracao-v2/relatorio.md): `llama3.1:8b` no Ollama local, prompt `extracao-v2`, 3 rodadas nos 7 casos de teste (21 extrações, cerca de 45 min). Ela é o ponto de comparação do change de melhoria do modelo do Ollama.

| Métrica | Linha de base |
|---|---|
| Validade | 0,29 (6 de 21: MFA e Reserva em todas as rodadas) |
| Válido na 1ª tentativa | 0,14 |
| Precisão / recall de estados | 0,19 / 0,13 |
| Precisão / recall de transições | 0,00 / 0,00 |
| Propriedades satisfeitas | 0,00 |
| Duração média | 124 s (sem timeouts) |

O que ela mostra:

- **A validação estrutural não basta.** Os modelos de MFA e Reserva passaram na validação, mas não satisfazem nenhuma propriedade. No MFA, o modelo junta as etapas: a senha correta não leva à etapa do código, e o código é aceito direto do estado inicial. Na Reserva, ela é confirmada só por haver quarto disponível, sem pagamento. É exatamente o tipo de erro semântico que motivou esta avaliação.
- **As falhas de validade vêm de regras reais do formato**, como datas em `valor_inicial` escritas como `"AAAA-MM-DD"` literalmente, finais com saída e guardas sobrepostas. A lista completa está em "Rodadas inválidas" no relatório.
- **As 3 rodadas de cada caso deram resultados idênticos** (desvio padrão 0 por caso), porque a extração usa temperatura 0 e semente fixa. Para medir variância de verdade, varie a semente (`QA_SEMENTE`) entre execuções; repetir rodadas com a mesma configuração só confirma o determinismo.
- **Pode haver sinônimos faltando**: por exemplo, o estado `AcessoConcedido` não foi casado com `Autenticado`. Eles não foram acrescentados depois de ver os resultados, para não ajustar o conjunto de teste à saída do modelo. Cabe à revisão em dupla (`benchmark/README.md`) decidir.
