# Tasks

## 1. Registro de provedores

- [x] 1.1 Criar `backend/provedores/` com `Capacidades`, o protocolo `Provedor`, `REGISTRO` e `ALIASES`; mover Ollama e Gemini para módulos próprios sem mudar comportamento; os testes atuais de Ollama e Gemini continuam passando
- [x] 1.2 Fazer `backend/llm.py` delegar ao registro, mantendo a assinatura de `chamar_llm` com o novo `modelo` opcional; teste com provedor falso registrado
- [x] 1.3 `Requisicao.motor` aceita id do registro ou rótulo legado e normaliza para o id; novo campo `modelo` opcional; testes de id, rótulo legado e provedor desconhecido (422 sem chamar LLM)
- [x] 1.4 Modelo por requisição prevalece sobre a variável de ambiente; teste com Ollama falso recebendo `qwen2.5:7b`

## 2. Provedor Anthropic

- [x] 2.1 Confirmar no índice do pip a versão 1.x publicada do `anthropic`, fixá-la no `requirements.txt` e instalar; `python -c "import anthropic"` funciona
- [x] 2.2 Implementar o provedor com `messages.create` + `output_config.format` (esquema de `anthropic.transform_schema(ModeloEstados)`; ver desvio no design), `max_retries=0`, timeout da tentativa, `effort` de `ANTHROPIC_EFFORT` e sem temperatura nem semente no `claude-opus-5-5`; teste com cliente falso confere os parâmetros enviados
- [x] 2.3 Converter recusa (`stop_reason == "refusal"`), 429, sobrecarga, 5xx, conexão e timeout em `ErroLLM`/`ErroTimeout` pelas classes tipadas do SDK; um teste por caso
- [x] 2.4 Enviar o fallback de recusa do servidor por padrão, desligável com `ANTHROPIC_FALLBACK_RECUSA=0`; teste dos dois modos
- [x] 2.5 Falta de credencial vira mensagem que cita `ANTHROPIC_API_KEY` sem fazer chamada; teste

## 3. Provedor compatível com OpenAI

- [x] 3.1 Adicionar a dependência `openai` e implementar o provedor com URL base, chave e modelo configuráveis; teste com cliente falso confere `base_url` e modelo
- [x] 3.2 Implementar os modos de esquema `json_schema`, `json_object` e `nenhum`; um teste por modo conferindo o `response_format` enviado
- [x] 3.3 URL base ausente gera erro de configuração sem chamada; 429/5xx/timeout convertidos como na Anthropic; testes
- [x] 3.4 Rodar uma extração real contra um servidor local compatível (LM Studio ou o endpoint `/v1` do próprio Ollama) e registrar o resultado no README

## 4. API, determinismo e saúde

- [x] 4.1 `ResultadoGeracao.deterministico` calculado pelas capacidades e devolvido em `/gerar`; teste de contrato com provedor determinístico e não determinístico
- [x] 4.2 `/saude` com uma entrada por provedor (configurado, modelo, disponibilidade), mantendo os campos do Ollama e sem expor chaves; teste com chaves definidas confere que o valor não aparece

## 5. Interface e avaliação

- [x] 5.1 Seletor de provedor a partir do registro, campo "Modelo" opcional e aviso de envio para a nuvem; testes com `AppTest` (lista de provedores, modelo enviado no corpo, aviso)
- [x] 5.2 `python -m avaliacao executar --provedor` aceita qualquer id do registro e passa o modelo na requisição; relatório e `config.json` registram se a execução foi determinística; testes com provedor falso
- [x] 5.3 Atualizar `.env.example` (sem chaves) e o README com os provedores novos, variáveis e cuidados de privacidade e custo; o teste de `.env.example` cobre as novas variáveis

## 6. Integração

- [x] 6.1 Rodar a avaliação no conjunto de desenvolvimento com o Claude (`--provedor anthropic`, 1 rodada, se houver credencial) e com um modelo via `openai_compat`, comparar com a linha de base usando `python -m avaliacao comparar` e registrar em `docs/avaliacao/`
