# Medição do fluxo real: `fsm-model-v2` (tarefa 5.1)

Execução em 2026-11-02, com o formato estendido do modelo, o prompt `extracao-v2` (temperatura 0, semente 42, saída restrita ao JSON Schema) e a validação nova. Mesmo procedimento da medição do `stabilize-pipeline`: cada rodada foi conduzida **pela interface** (`AppTest`, modo demonstração desligado) contra uma instância própria da API, com chamadas reais aos provedores.

Configuração: `QA_TIMEOUT_LLM=180`, `QA_ORCAMENTO_GERACAO=360`, 3 tentativas, `OLLAMA_MODEL=llama3.1:8b` (aquecido), `GEMINI_MODEL=gemini-3.8-flash`. Login e Saque usam o catálogo do sistema exemplo (sem variáveis); Cupom, MFA e Carrinho são extração livre (com variáveis e guardas permitidas).

## Ollama (`llama3.1:8b`)

| Exemplo | Passou na validação? | Tentativas | Tempo | Detalhe |
|---|---|---|---|---|
| Login bancário (catálogo) | **Sim** | 2 (inválida 51 s, válida 34 s) | 87 s | 5 estados, 4 transições; execução: **Bug detectado** |
| Saque em caixa eletrônico (catálogo) | Não | 3 | 162 s | Último erro: `final_com_saida`, porque `EntregandoNotas` foi marcado como final e tem saída |
| Cupom Promocional (livre) | Não | 3 | 184 s | 8 erros na última tentativa, entre eles `guardas_sobrepostas` entre `cupom_valido e data_atual <= validade` e `cupom_expirado` |
| Autenticação MFA (livre) | **Sim** | 1 | 38 s | 3 estados, 4 transições |
| Carrinho de Compras (livre) | **Sim** | 2 (inválida 40 s, válida 34 s) | 76 s | 3 estados, 4 transições |

**3 de 5 exemplos passaram na validação**, contra 0 de 5 na medição do `stabilize-pipeline` com o formato antigo. Nesta máquina, as rodadas ficaram entre 38 s e 184 s, sem nenhum timeout.

## Gemini (`gemini-3.8-flash`)

Nenhuma rodada chegou ao modelo. Quatro exemplos receberam `429 RESOURCE_EXHAUSTED` (cota da chave esgotada) e o Saque recebeu `503 UNAVAILABLE` (alta demanda). Todas as falhas apareceram na interface como erro 502 legível, em 3 a 8 s. A cota foi consumida pelas medições anteriores do dia, então os resultados do Gemini ficam para uma próxima rodada.

## O que a medição mostra

1. **O formato estendido e a correção guiada funcionam com um modelo de 8B.** Em Login e Carrinho, a primeira resposta foi inválida e a segunda, corrigida a partir dos erros agrupados e do modelo anterior, passou. As falhas de "transição ambígua" da medição anterior (Cupom e Carrinho) deram lugar a guardas.
2. **A validação nova barra erros reais.** No Saque, o LLM marcou um estado intermediário como final em todas as tentativas. No Cupom, criou duas variáveis booleanas independentes (`cupom_valido`, `cupom_expirado`) cujas guardas podiam ser verdadeiras ao mesmo tempo, e a análise por valores de fronteira mostrou a valoração que causa a sobreposição.
3. **Com catálogo, o modelo válido é fiel ao sistema.** O Login extraído gerou testes que passaram na variante correta e detectaram o bug.
4. **Nenhuma exceção na interface** nas 10 rodadas.
5. **Pontos para os próximos changes:**
   - O catálogo não informa quais estados são finais. Indicar os finais no catálogo poderia evitar o erro do Saque.
   - A avaliação semântica (`add-reference-evaluation`) é o próximo passo para saber se os modelos válidos de MFA e Carrinho estão corretos, e não só bem formados.
   - Estes números são de uma única rodada por exemplo. A variância fica para o executor de avaliação.
