# 🤖 QA Autonomous — Geração de Testes com PLN e MBT

> **Projeto Semestral — Processamento de Linguagem Natural (PLN)**  
> **Instituição:** Faculdade de Tecnologia de Cotia (Fatec Cotia)  
> **Autor:** Juan Cezar Yghor Andrade

Transforma **User Stories** e **Critérios de Aceite** em um modelo de estados e, a partir dele, em **testes executáveis**. O LLM extrai o modelo; os caminhos, o Gherkin e o Pytest são gerados por código determinístico, cobrindo todas as transições.

---

## 📌 Como funciona

```text
Requisitos --> LLM + catálogo --> Modelo --> Validação --> Caminhos --> .feature + Pytest
                                    ^            |                            |
                                    +-- retry ---+                            v
                                                              Sistema correto e sistema com bug
                                                                              |
                                                                              v
                                                                          Veredito
```

Os testes rodam contra **sistemas exemplo** reais, em `sistemas_exemplo/`: Login bancário e Saque em caixa eletrônico. Cada um tem uma variante correta e uma com bug injetado, o que mostra que os testes detectam falhas de verdade.

---

## 🚦 Status do Projeto

| Componente | Status | Descrição |
| :--- | :---: | :--- |
| **Interface (Streamlit)** | ✅ Entregue | Entrada de requisitos, grafo, métricas, artefatos e execução. |
| **Extração do modelo com LLM** | ✅ Entregue | Gemini validado com catálogo; 5 de 6 rodadas concluíram na medição. |
| **Geração de testes** | ✅ Entregue | Gherkin e Pytest executáveis, cobrindo todas as transições. |
| **Execução e veredito** | ✅ Entregue | Roda nas duas variantes e separa erro do modelo de bug do sistema. |
| **Ollama local** | 🟡 Parcial | Depende de memória: `llama3.1:8b` não concluiu na máquina medida. |
| **Histórico (SQLite)** | ⏳ Não iniciado | Fora do escopo atual. |
| **Testes de aplicações web** | ⏳ Não iniciado | Fora do escopo atual. |

---

## 🚀 Como Executar

### 1. Instalação

Requer **Python 3.10** ou superior.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Modo demonstração

Não precisa de chave nem de backend. O grafo usa o Mermaid por CDN, então exige internet.

```bash
streamlit run app.py
```

Abra `http://localhost:8501`, escolha **Login bancário** ou **Saque em caixa eletrônico**, clique em **🚀 Gerar Modelo e Testes** e depois em **▶️ Executar testes nas duas variantes**.

Na demonstração, o modelo é o de referência do sistema exemplo ou o gabarito do exemplo, e todas as abas mostram o aviso *"Demonstração: modelo de referência, sem LLM"*. A demonstração só exibe exemplos **sem edição**; texto digitado ou editado exige desativar o modo demonstração. Cupom Promocional, Autenticação MFA e Carrinho de Compras ainda não têm sistema exemplo, então mostram o gabarito (com variáveis e guardas) e geram testes como esqueleto.

### 3. Modo real, com LLM

```bash
# Windows: copy .env.example .env
cp .env.example .env
```

Preencha `GEMINI_API_KEY` **apenas no `.env`**, que é ignorado pelo Git. Nunca coloque a chave no `.env.example`. Depois, em dois terminais:

```bash
uvicorn backend.main:app --reload
```

```bash
streamlit run app.py
```

Desative o **Modo demonstração** na barra lateral e escolha o **Motor LLM**. O provedor é escolhido a cada geração. O campo **Modelo (opcional)** troca o modelo só daquela geração; se ficar vazio, vale o do `.env`.

Para usar o Ollama, instale o modelo configurado (`ollama pull llama3.1:8b`). Ao subir, a API confere se ele está instalado e o carrega na memória (aquecimento). Para ver a situação:

```bash
curl http://localhost:8000/saude
```

A resposta informa o modelo de cada provedor, se o modelo do Ollama está disponível (com a lista de instalados, quando não está), se o aquecimento terminou (`"situacao": "pronto"`) e se há chave do Gemini configurada, sem mostrar a chave.

### Configuração

| Variável | Padrão | Uso |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | — | Chave do Gemini. Também pode ser informada na barra lateral. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Modelo do Gemini. |
| `OLLAMA_MODEL` | `llama3.1:8b` | Modelo do Ollama. Use o nome com a tag. |
| `OLLAMA_HOST` | `http://localhost:11434` | Endereço do Ollama. |
| `QA_TIMEOUT_LLM` | `180` | Tempo limite de **cada** chamada ao LLM, em segundos. |
| `QA_ORCAMENTO_GERACAO` | `360` | Tempo total de uma geração, somando as tentativas. A interface espera esse valor + 15 s. |
| `QA_OLLAMA_KEEP_ALIVE` | `30m` | Por quanto tempo o Ollama mantém o modelo na memória após o aquecimento. |
| `QA_SEMENTE` | `42` | Semente da extração (Ollama, Gemini e servidor compatível), usada junto com temperatura 0. |
| `ANTHROPIC_API_KEY` | — | Chave da Anthropic (Claude). Só no `.env`. |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | Modelo do Claude. |
| `ANTHROPIC_EFFORT` | `medium` | Esforço do modelo (`low` a `max`); vazio não envia. |
| `ANTHROPIC_FALLBACK_RECUSA` | `1` | Se o Claude recusar por segurança, a API reexecuta em outro modelo Claude. `0` desliga. |
| `OPENAI_COMPAT_BASE_URL` | — | URL de um servidor compatível com OpenAI (ex.: `http://localhost:1234/v1`). |
| `OPENAI_COMPAT_API_KEY` | — | Chave desse servidor; vazia em servidores locais. |
| `OPENAI_COMPAT_MODEL` | — | Modelo no servidor compatível. |
| `OPENAI_COMPAT_MODO_ESQUEMA` | `json_schema` | `json_schema` (esquema estrito), `json_object` (só JSON) ou `nenhum`. |
| `OPENAI_COMPAT_DETERMINISTICO` | `0` | `1` se o servidor respeita temperatura 0 e semente. |

### Provedores de LLM

| Provedor (`motor`) | Onde roda | Saída restrita ao esquema | Determinístico | Configuração mínima |
| :--- | :--- | :---: | :---: | :--- |
| `ollama` (padrão) | Local | ✅ | ✅ | Ollama rodando e `ollama pull llama3.1:8b` |
| `gemini` | Nuvem (Google) | ✅ | ✅ | `GEMINI_API_KEY` |
| `openai_compat` | Local ou nuvem, conforme a URL | Conforme o modo | Se declarado | `OPENAI_COMPAT_BASE_URL` e `OPENAI_COMPAT_MODEL` |
| `anthropic` | Nuvem (Anthropic) | ✅ | ❌ | `ANTHROPIC_API_KEY` |

- **Servidor compatível com OpenAI:** serve para LM Studio, vLLM, llama.cpp server, OpenRouter, Groq e Together. Teste feito em 2026-11-03 contra o endpoint `/v1` do próprio Ollama (`OPENAI_COMPAT_BASE_URL=http://localhost:11434/v1`, `OPENAI_COMPAT_MODEL=llama3.1:8b`, modo `json_schema`): o exemplo Login gerou um modelo válido na 2ª tentativa, em 69 s.
- **Claude:** `claude-opus-5-5` não aceita temperatura nem semente, então a extração não é determinística, e a resposta de `/gerar` traz `"deterministico": false`. Para comparar com outros modelos, use rodadas repetidas na avaliação.
- **Privacidade:** com provedores na nuvem, os requisitos digitados saem da máquina. A interface avisa quando o provedor escolhido é de nuvem.
- **Custo e cota:** Gemini, Claude e serviços como OpenRouter cobram por uso. Na avaliação, comece com `--casos` e `--rodadas 1`.
- **Saúde:** `curl http://localhost:8000/saude` mostra, para cada provedor, se está configurado, o modelo e a disponibilidade, sem mostrar chaves.
- **Compatibilidade:** os rótulos antigos `"Ollama (Local)"` e `"Gemini (Cloud)"` continuam aceitos em `motor`.
| `QA_AQUECER_OLLAMA` | `1` | Use `0` para não aquecer o Ollama ao subir a API. |
| `QA_API_URL` | `http://localhost:8000` | Endereço do backend. |

### Importar requisitos de um arquivo

Na interface, **📂 Importar arquivo** aceita `.txt` ou `.md` com duas seções (maiúsculas e acentos não importam):

```markdown
# História
Como cliente, quero sacar dinheiro no caixa eletrônico, para ter dinheiro em espécie.

# Critérios
1. Saque com saldo suficiente entrega as notas.
2. Saque sem saldo é recusado.
```

Edições feitas nos campos depois da importação prevalecem. Critérios sem número são numerados de 1 a N antes do envio, e a lista numerada aparece abaixo do campo.

### Erros da API

Todo erro de `POST /gerar` vem como JSON `{"codigo": ..., "mensagem": ...}`:

| Status | Código | Quando |
| :--- | :--- | :--- |
| 422 | `entrada_invalida` | Campos vazios, acima de 2000 caracteres, critérios sem numeração ou sistema desconhecido. |
| 422 | `modelo_invalido` | O LLM não produziu um modelo válido em 3 tentativas. |
| 502 | `falha_provedor` | Erro do provedor, por exemplo chave ausente ou Ollama desligado. |
| 504 | `orcamento_esgotado` | O orçamento de tempo acabou antes de um modelo válido. |
| 500 | `erro_interno` | Erro inesperado no backend. |

Com sucesso, a resposta traz `modelo`, `tentativas`, `duracao` e o `historico` de cada tentativa (`valido`, `invalido` ou `timeout`).

---

## 🧩 Modelo de estados

O LLM extrai um modelo de estados finito estendido em JSON (prompt `extracao-v2`, temperatura 0, semente `QA_SEMENTE`, saída restrita ao JSON Schema):

| Campo | Conteúdo |
| :--- | :--- |
| `analise` | Primeiro campo: as regras identificadas em cada critério, antes do modelo. |
| `variaveis` | `nome` (snake_case), `tipo` (`inteiro`, `decimal`, `booleano`, `data`) e `categoria`: **estado** (muda por ações, tem `valor_inicial`), **entrada** (vem com o evento) ou **contexto** (fixa no cenário). |
| `estados` | `id` em PascalCase ASCII, `rotulo` livre em português e `tipo` (`inicial`, `intermediario`, `final`). |
| `transicoes` | `id`, `de`, `evento` (snake_case), `para`, `guarda`, `acoes` e `criterios` (lista de números). |

Guardas usam variáveis, literais, `+ - %`, comparações e `e`/`ou`/`não` (ex.: `valor <= saldo e valor % 20 == 0`). Ações só alteram variáveis de estado (`tentativas += 1`). Tudo é interpretado sem `eval`.

A validação devolve **todos** os erros de uma vez, com código e mensagem, e eles voltam ao LLM junto com o modelo anterior: inicial único, ao menos um final, finais sem saída, todo estado alcançável e com caminho até um final, referências e tipos válidos, todos os critérios cobertos e nenhuma sobreposição de guardas no mesmo estado e evento (verificada por valores de fronteira).

Os sistemas exemplo (Login e Saque) não têm variáveis no catálogo, então contam tentativas com estados (`UmaFalha`, `DuasFalhas`). Os gabaritos de `exemplos/` (Cupom, MFA, Carrinho e Saque ATM) usam variáveis e guardas e aparecem na demonstração. Por enquanto, os caminhos de teste ainda ignoram as guardas, então modelos com guardas geram apenas esqueletos.

## 📏 Avaliação da extração

A validação garante que o modelo é bem formado, mas não que ele está certo. Para medir isso, `benchmark/` tem 15 casos com modelo gabarito e propriedades comportamentais (ex.: "um PIN errado não retém o cartão"), separados em desenvolvimento e teste:

```bash
python -m avaliacao casos
python -m avaliacao executar --provedor ollama --modelo llama3.1:8b --rodadas 3 --conjunto teste
python -m avaliacao comparar resultados/<execucao-a> resultados/<execucao-b>
```

O relatório traz validade, precisão e recall de estados e transições, propriedades satisfeitas e latência, com média e desvio padrão. Detalhes em [`docs/avaliacao/README.md`](docs/avaliacao/README.md).

## 🎯 Sistema alvo e veredito

O **Sistema alvo** é escolhido na barra lateral. Com um sistema selecionado, o LLM recebe o catálogo de estados e eventos e deve usar somente esses nomes. Sem sistema, o modelo usa nomes livres e os artefatos são **esqueletos**: os testes falham até um sistema real ser conectado.

A execução sempre roda as duas variantes, e a variante correta é tratada como verdade:

| Sistema correto | Sistema com bug | Veredito | Significado |
| :--- | :--- | :--- | :--- |
| Passou | Falhou | **Bug detectado** | Os testes funcionam. |
| Passou | Passou | **Bug não detectado** | Os testes são insuficientes. |
| Falhou | Qualquer | **Modelo diverge do sistema** | O modelo gerado está errado. |
| Erro | Qualquer | **Erro de execução** | Os testes não rodaram. |
| Passou | Erro | **Erro de execução** | Os testes não rodaram. |

### Rodar os arquivos baixados

Salve o `.feature` e o script em uma mesma pasta dentro do projeto e rode, a partir da raiz:

```bash
python -m pytest <pasta>
```

Para rodar contra a variante com bug, defina `QA_VARIANTE=bug` antes do comando.

---

## 🧪 Testes do Projeto

```bash
python -m pytest tests
```

A suíte cobre os sistemas exemplo, a validação, a geração, a execução e a interface. Nenhum teste chama um LLM real.

---

## 📁 Estrutura do Repositório

```text
qa_auto/
├── app.py                # Interface Streamlit
├── demo_data.py          # Exemplos da barra lateral e modelos da demonstração
├── requirements.txt
├── pytest.ini
│
├── backend/
│   ├── main.py           # API FastAPI (/gerar, /saude, erros padronizados)
│   ├── schemas.py        # Entrada e modelo de estados (ModeloEstados)
│   ├── expressoes.py     # Linguagem de guardas e ações (interpretador sem eval)
│   ├── entrada.py        # Numeração de critérios, importação e validação na interface
│   ├── prompts/          # Prompt versionado (extracao_v2.md) e montagem das mensagens
│   ├── llm.py            # Fachada dos provedores e saúde do Ollama
│   ├── provedores/       # Registro: ollama, gemini, openai_compat, anthropic
│   ├── servico.py        # Extração com retry e orçamento de tempo
│   ├── validacao.py      # Regras do modelo, com todos os erros de uma vez
│   ├── geracao.py        # Caminhos, Gherkin, Pytest e grafo
│   └── execucao.py       # Execução e veredito
│
├── sistemas_exemplo/     # Sistemas alvo dos testes
│   ├── base.py
│   ├── login.py
│   └── saque.py
│
├── exemplos/             # Gabaritos (história + modelo escrito à mão) em JSON
├── benchmark/            # 15 casos de referência (YAML) com propriedades comportamentais
├── avaliacao/            # Avaliação da extração: python -m avaliacao
├── docs/                 # Medições, linha de base da avaliação e roadmap
│
└── tests/
```

---

## 🛠️ Tecnologias

- **Streamlit** e **Mermaid.js:** interface e grafo de estados.
- **FastAPI** e **Pydantic:** API e validação.
- **Gemini** e **Ollama:** extração do modelo.
- **pytest** e **pytest-bdd:** execução dos testes gerados.

---

## 👨‍💻 Autor

- **Juan Cezar Yghor Andrade**  
- Curso de Análise e Desenvolvimento de Sistemas — Fatec Cotia  
- Disciplina: *Processamento de Linguagem Natural (PLN)*
