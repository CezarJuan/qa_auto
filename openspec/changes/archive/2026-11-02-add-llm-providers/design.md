# Design

## Context

Ver proposal.md (Why). Estado atual:

- `backend/llm.py` tem `_chamar_gemini` e `_chamar_ollama`, despachados por `chamar_llm(motor, ...)` com os rótulos "Gemini (Cloud)" e "Ollama (Local)". `nome_do_modelo(motor)` lê `GEMINI_MODEL` ou `OLLAMA_MODEL`.
- `Requisicao.motor` é um `Literal` desses dois rótulos. `app.py` tem um `selectbox` fixo, e `avaliacao/executor.py` tem `PROVEDORES = {"ollama": ..., "gemini": ...}`, que troca o modelo por variável de ambiente durante a execução.
- `servico.gerar` chama `chamar(motor, system, mensagens, api_key=..., timeout=...)`, trata `ErroTimeout` como tentativa e propaga os demais `ErroLLM`. Todos os testes usam fakes com essa assinatura.
- O esquema de saída é `ModeloEstados.model_json_schema()`, com `pattern` nos ids e uniões de tipo em `valor_inicial`. Ollama e Gemini recebem temperatura 0 e semente `QA_SEMENTE`.

## Goals / Non-Goals

**Goals:**
- Adicionar um provedor exige um módulo novo e uma linha no registro, sem mexer em interface, API ou avaliação.
- Comparar modelos de provedores diferentes no mesmo benchmark.

**Non-Goals:**
- Fallback entre provedores e escalonamento por qualidade (fora do escopo, por decisão do usuário).
- Streaming de resposta. A extração tem saída curta (~750 tokens), e a resposta só é útil inteira.

## Decisions

### 1. Registro em `backend/provedores/`

```python
@dataclass(frozen=True)
class Capacidades:
    esquema: bool        # aceita saída restrita a JSON Schema
    temperatura: bool    # aceita temperatura 0
    semente: bool        # aceita semente

class Provedor(Protocol):
    id: str
    nome: str
    def modelo_padrao(self) -> str: ...
    def capacidades(self, modelo: str) -> Capacidades: ...
    def saude(self) -> dict: ...                      # sem segredos
    def chamar(self, system, mensagens, *, modelo, timeout, esquema, api_key=None) -> str: ...

REGISTRO = {p.id: p for p in (Ollama(), Gemini(), OpenAICompat(), Anthropic())}
ALIASES = {"Ollama (Local)": "ollama", "Gemini (Cloud)": "gemini"}
```

`backend/llm.py` mantém `chamar_llm(motor, system, mensagens, api_key=None, timeout=None, modelo=None)` como fachada sobre o registro, então os fakes dos testes e o `servico` continuam funcionando. `ErroLLM` e `ErroTimeout` continuam sendo as únicas exceções que saem de um provedor. As capacidades dependem do modelo, porque na Anthropic a temperatura é aceita ou não conforme a geração do modelo.

Alternativa descartada: LiteLLM ou outra camada genérica. Ela traz dezenas de provedores, mas esconde parâmetros como `format` do Ollama, `output_config` da Anthropic e o modo de esquema, que são exatamente o que importa para a qualidade da extração.

### 2. Anthropic pelo SDK oficial

- Dependência `anthropic` 1.x, que usa `httpx2` e não conflita com o `httpx` do Ollama.
- Chamada `client.messages.create(..., output_config={"format": {"type": "json_schema", "schema": anthropic.transform_schema(ModeloEstados)}, "effort": ...})`. O `transform_schema` do SDK move para a descrição o que a API não suporta (como `pattern`), e o provedor devolve o **texto cru** para a validação do projeto, que continua sendo a fonte da verdade. *Desvio do plano inicial (`messages.parse`)*: o `parse` lança exceção quando a saída não valida no Pydantic e perde o texto. Com o texto cru, a validação do projeto produz os erros agrupados que voltam ao LLM na correção.
- Modelo padrão `claude-opus-5-5`, configurável por `ANTHROPIC_MODEL` ou na requisição.
- Nesse modelo, **temperatura e semente retornam 400** e o thinking não pode ser desligado. `capacidades()` declara isso, e o provedor só envia `output_config={"effort": ANTHROPIC_EFFORT}` (padrão `medium`, configurável).
- Cliente com `timeout=limite da tentativa` e `max_retries=0`. As novas tentativas do SDK (padrão 2) multiplicariam o tempo e furariam o orçamento. As falhas viram mensagens claras (decisão 4).
- `stop_reason == "refusal"` vira `ErroLLM` com a categoria de `stop_details`. Por recomendação da Anthropic para o Opus 5.5, o provedor envia o fallback de recusa do próprio servidor (`fallbacks: "default"` com o beta `server-side-fallback-2026-07-01`), que reexecuta a mesma requisição em outro modelo Claude só quando há recusa. É uma opção da API da Anthropic e não o fallback entre provedores que ficou fora do escopo. Pode ser desligado com `ANTHROPIC_FALLBACK_RECUSA=0`.
- A credencial segue a ordem do SDK (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, perfil de `ant auth login`). A falta de credencial vira `ErroLLM` que cita `ANTHROPIC_API_KEY`.

### 3. Provedor compatível com OpenAI

- Dependência `openai`, cliente oficial do protocolo, configurada com `base_url=OPENAI_COMPAT_BASE_URL` e `api_key=OPENAI_COMPAT_API_KEY` (servidores locais aceitam qualquer valor; o provedor usa um marcador fixo quando a chave está vazia).
- O suporte a esquema varia entre servidores, então `OPENAI_COMPAT_MODO_ESQUEMA` escolhe o formato:
  - `json_schema` (padrão): `response_format={"type": "json_schema", "json_schema": {"name": "modelo_estados", "schema": ..., "strict": true}}`;
  - `json_object`: só JSON;
  - `nenhum`: só o prompt.

  As capacidades informam qual modo foi usado.
- Temperatura 0 e semente são enviadas, porque o protocolo aceita os dois, mas servidores podem ignorar a semente. O resultado registra a extração como determinística só no modo de chamada local declarado pelo usuário (`OPENAI_COMPAT_DETERMINISTICO=1`).

### 4. Erros transitórios

Cada provedor converte as próprias exceções em `ErroLLM`, com a mensagem `"<Provedor>: <tipo> (<status>)"`:

| Erro | Mensagem |
|---|---|
| 429 / limite de taxa | limite de taxa |
| 529 / sobrecarregado | sobrecarregado, tente de novo ou troque de provedor |
| 5xx | indisponível |
| Timeout | `ErroTimeout` (vira tentativa, como hoje) |

Na Anthropic, a conversão usa as classes tipadas do SDK (`RateLimitError`, `APIStatusError`, `APIConnectionError`, `APITimeoutError`), em ordem do mais específico ao mais geral, e não por texto. O `servico` não muda: `ErroLLM` vira 502, e `ErroTimeout` conta no orçamento.

### 5. Modelo por requisição e determinismo

- `Requisicao` ganha `modelo: str | None` e `motor` passa a ser `str`, validado contra `REGISTRO` e `ALIASES` e normalizado para o id.
- `ResultadoGeracao` ganha `deterministico: bool`, calculado pelas capacidades do provedor e do modelo, e `/gerar` o devolve.
- `nome_do_modelo` passa a considerar o modelo da requisição.
- A avaliação troca a variável de ambiente pelo `modelo` na requisição, mantendo o nome da pasta de resultados.

### 6. Interface

O seletor "Motor LLM" lista `REGISTRO` (nome de exibição), com um campo de texto opcional "Modelo" cujo placeholder é o padrão do provedor. Para provedores na nuvem, uma legenda avisa que os requisitos serão enviados ao provedor. A chave do Gemini informada na barra lateral continua só para o Gemini; os provedores novos leem as chaves do `.env`.

## Risks / Trade-offs

- [O Claude não é determinístico, porque não aceita temperatura e semente] → O resultado e o relatório marcam isso. Na avaliação, as rodadas repetidas passam a medir variância de verdade.
- [O thinking sempre ligado e o effort aumentam a latência e o custo do Claude] → `ANTHROPIC_EFFORT` configurável (`low` para comparar) e o custo medido pelo benchmark antes de adotar como padrão.
- [Servidores compatíveis com OpenAI ignoram ou rejeitam `json_schema`] → Modo de esquema configurável, e a validação do projeto continua obrigatória.
- [Cota e custo dos provedores pagos] → Avaliação com `--casos` para subconjuntos, e o executor já mostra uma estimativa antes de começar.
- [Dados do usuário saem da máquina com provedores na nuvem] → Aviso na interface. Ollama continua como padrão.

## Migration Plan

Os rótulos antigos de `motor` continuam aceitos, então clientes existentes, inclusive o front atual e a linha de base da avaliação, não quebram. Novas variáveis entram no `.env.example` sem chave. Para reverter, basta remover os provedores novos do registro.
