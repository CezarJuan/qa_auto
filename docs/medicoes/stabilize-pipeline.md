# Medição do fluxo real: `stabilize-pipeline` (tarefa 6.2)

Execução em 2026-11-02, com o código deste change. Cada rodada foi conduzida **pela interface** (Streamlit `AppTest`, modo demonstração desligado) contra uma instância própria da API (`uvicorn backend.main:app`), com chamadas reais aos provedores. Um wrapper sobre o `requests.post` registrou status, código de erro e histórico de tentativas.

Configuração: `QA_TIMEOUT_LLM=180`, `QA_ORCAMENTO_GERACAO=360` (a interface espera 375 s), 3 tentativas, `OLLAMA_MODEL=llama3.1:8b` (aquecido no startup, `/saude` com `situacao: pronto`), `GEMINI_MODEL=gemini-3.8-flash`. Os 5 exemplos usam os critérios numerados da barra lateral. Login e Saque têm sistema alvo (com catálogo); Cupom, MFA e Carrinho não.

## Resultado

### Ollama (`llama3.1:8b`, local)

| Exemplo | Status | Código | Tempo | Detalhe |
|---|---|---|---|---|
| Login bancário | 504 | `orcamento_esgotado` | 364 s | 2 tentativas; a 2ª recebeu só o restante do orçamento (178 s) e estourou |
| Saque em caixa eletrônico | 422 | `modelo_invalido` | 128 s | 3 tentativas; último erro: `AguardandoCartao` + `InserirCartao` com dois destinos |
| Cupom Promocional | 422 | `modelo_invalido` | 81 s | 3 tentativas; `Aplicar cupom` leva a `CupomVálido` e `CupomExpirado` |
| Autenticação MFA | 422 | `modelo_invalido` | 121 s | 3 tentativas; critérios 3 e 4 sem transição |
| Carrinho de Compras | 422 | `modelo_invalido` | 348 s | 3 tentativas; `Remover item` leva a `CarrinhoVazio` e `CarrinhoComItens` |

### Gemini (`gemini-3.8-flash`), duas rodadas

| Exemplo | Rodada 1 | Rodada 2 |
|---|---|---|
| Login bancário | 502: serviço respondeu 503 *high demand* (6 s) | 502: 503 *high demand* (5 s) |
| Saque em caixa eletrônico | 502: 503 *high demand* (6 s) | 504: duas tentativas com `504 DEADLINE_EXCEEDED` do Gemini, orçamento esgotado (360 s) |
| Cupom Promocional | 502: 503 *high demand* (10 s) | **200**: 2 tentativas (timeout em 179 s, depois válido em 50 s); 5 estados, 4 transições; total 232 s |
| Autenticação MFA | 502: 503 *high demand* (6 s) | 502: 503 *high demand* (40 s) |
| Carrinho de Compras | 502: 503 *high demand* (189 s) | 502: 503 *high demand* (34 s) |

As duas rodadas se sobrepuseram no tempo em um ponto (Carrinho da rodada 1 e Login da rodada 2), o que pode ter contribuído para a lentidão nesse intervalo.

## O que a medição mostra

1. **Nenhum erro sem tratamento na interface.** Nas 15 rodadas, `AppTest` não registrou nenhuma exceção. Todos os erros apareceram como mensagem legível, com o status (422, 502 e 504).
2. **O orçamento único funciona.** Nos dois casos de 504, a última tentativa recebeu só o restante do orçamento, e a geração terminou em 360–364 s, enquanto a interface ainda aguardava (limite de 375 s).
3. **Timeouts são registrados e não encerram a geração.** No Cupom com Gemini, a 1ª tentativa estourou (`timeout`), e a 2ª produziu um modelo válido dentro do orçamento. O `504 DEADLINE_EXCEEDED` do Gemini também é tratado como timeout.
4. **O `llama3.1:8b` não produziu modelo válido em nenhum exemplo.** Desta vez o Ollama rodou na máquina (diferente da medição de 2026-11-01). Três das cinco falhas são "transição ambígua" em situações que dependem de condição (cupom válido ou expirado; remover item com 1 ou mais itens). O formato atual do modelo não consegue representar isso sem guardas, que é o motivo do change `fsm-model-v2`. Isso serve de linha de base para ele.
5. **O Gemini esteve majoritariamente indisponível** (503 *high demand*) durante a medição. Isso é instabilidade do serviço, não falha do código, mas mostra que 503 hoje não é repetido. Avaliar retry com espera para 503 do provedor em um change futuro, fora do escopo deste.

## Como reproduzir

Com o Ollama rodando e a chave do Gemini no `.env`:

```bash
uvicorn backend.main:app --port 8766
```

Em seguida, conduza a interface com `QA_API_URL=http://localhost:8766`, um exemplo por vez, com o modo demonstração desligado, ou chame `POST /gerar` diretamente com os textos de `demo_data.py`.
