# Design

## Context

Hoje o backend FastAPI devolve apenas um `ModeloMBT`, e o front Streamlit monta o restante da tela. O modo demonstração precisa funcionar sem backend, então qualquer lógica compartilhada entre os dois modos não pode depender de HTTP.

Evidências que moldam o desenho, obtidas no discovery:

- O LLM varia nomes entre rodadas e produz modelos logicamente errados que passam na validação atual.
- O Mermaid 10 divide `Com itens` em dois estados sem erro, e falha com hífen; aceita acentos.
- Com `llama3.1:8b`, 3 de 6 rodadas estouraram o timeout de 90s; o caso Login nunca concluiu. A amostra é pequena e pode refletir carga inicial ou fila.
- Protótipo com `pytest-bdd` 9.0.0 confirmou passos genéricos, `When`/`Then` alternados, seleção de variante por ambiente e motivo de falha no JUnit XML.

Motivação e escopo: ver `proposal.md`. Comportamento: ver `specs/`.

## Goals / Non-Goals

**Goals:**

- Um único caminho de geração para demonstração, modo real e esqueleto.
- Separar erro do modelo de bug do sistema sem análise manual.
- Manter o script gerado sem nenhum texto vindo do modelo.

**Non-Goals:**

- Eventos inválidos como casos de teste negativos: só transições do modelo são exercitadas.
- Otimizar o número de passos: caminhos curtos são preferidos a uma cobertura mínima.
- Isolamento de segurança na execução: roda localmente e o script não contém texto externo.
- Corrigir `TypeError` engolido em `servico.py` e bugs do upload: ficam para outra change.

## Decisions

### 1. Sistemas exemplo como pacote na raiz

`sistemas_exemplo/` fica fora de `backend/`, porque representa o sistema sob teste, não a ferramenta. O script gerado o importa, então precisa ser importável sem carregar FastAPI.

```
sistemas_exemplo/
  __init__.py   # SISTEMAS, criar(id, variante)
  base.py       # Catalogo, SistemaExemplo, erros
  login.py      # catálogo, Login, LoginComBug, referência, requisitos
  saque.py      # catálogo, Saque, SaqueComBug, referência, requisitos
```

Cada classe guarda regra de negócio de verdade (`falhas`, `saldo`) e deriva `estado` dela, em vez de consultar uma tabela de transições. Uma tabela igual ao modelo faria o teste comparar o modelo com ele mesmo. `disparar(evento)` traduz o evento do catálogo para a operação de negócio.

Bugs injetados:

- `login`: a terceira senha errada não bloqueia a conta (critério 3).
- `saque`: saque sem saldo entrega as notas (critério 2).

Alternativa rejeitada: contador como guarda no modelo. Exigiria extrair variáveis e condições do texto, aumentando o que o LLM pode errar. Estados desdobrados mantêm uma máquina finita simples. O custo é só escalar para contagens pequenas, suficiente para este escopo.

### 2. Catálogo no prompt e na validação

`Requisicao` ganha `sistema: str | None`. `gerar_modelo` busca o catálogo e o repassa a `montar_user_prompt` e a `validar_resposta`, de modo que o erro de catálogo reutiliza o retry existente. O catálogo inclui descrições para o LLM relacionar "senha correta" a `SenhaCorreta`.

Alternativa rejeitada: mapear nomes depois da extração. Um mapeamento errado apareceria como bug do sistema, confundindo o veredito.

### 3. Geração determinística e sem texto do modelo no script

Novo módulo puro `backend/geracao.py`, sem dependência de LLM ou FastAPI:

- `gerar_caminhos(modelo)`: para cada transição ainda não coberta, na ordem do modelo, faz BFS do inicial até a origem dela, percorrendo vizinhos na ordem das transições, e acrescenta a transição. Tudo que o caminho percorre conta como coberto.
- `gerar_feature(modelo, caminhos, titulo)`: um cenário por caminho.
- `gerar_script(nome_feature, sistema_id)`: um script fixo, com três passos genéricos parametrizados.

```gherkin
Scenario: Caminho 2 - critérios 2, 3
  Given que o sistema está no estado "SemFalha"
  When ocorre o evento "SenhaIncorreta"
  Then o estado deve ser "UmaFalha"
```

Como os passos são genéricos, nunca há passo ausente, e o script depende só do nome do arquivo e do id do sistema, ambos controlados pela ferramenta. Assim, texto do modelo vai só para o `.feature`. No Gherkin, eventos são normalizados (espaços colapsados, aspas removidas), o título vem do sistema e os requisitos não são copiados.

Sem sistema, o mesmo script recebe uma fixture `sut` que falha informando que falta conectar o sistema.

Alternativas rejeitadas: gerar testes com o LLM, que seria não determinístico e tornaria a cobertura impossível de garantir; e passos específicos por transição, que exigiriam inserir texto do modelo em código.

### 4. Geração e execução no processo do front

O front chama `backend.geracao` e `backend.execucao` diretamente, nos dois modos. A API continua responsável só por extrair o modelo. Assim, a demonstração funciona sem backend e não há dois caminhos de geração.

Alternativa rejeitada: novos endpoints HTTP. Exigiriam o backend ativo na demonstração ou duplicariam a lógica.

### 5. Execução em subprocesso, sobre as duas variantes

`backend/execucao.py` escreve os artefatos em um diretório temporário e roda, para cada variante, `sys.executable -m pytest` com `--junitxml`, `-p no:cacheprovider`, `QA_VARIANTE` e `PYTHONPATH` apontando para a raiz do projeto, com timeout de 60s. O resultado por cenário vem do JUnit XML; ausência do XML ou zero testes coletados contam como erro de execução.

A variante correta é tratada como verdade, o que dá o veredito sem interpretar o texto da falha:

| Variante correta | Variante com bug | Veredito |
|---|---|---|
| passou | falhou | Bug detectado |
| passou | passou | Bug não detectado |
| falhou | qualquer | Modelo diverge do sistema |
| erro | qualquer | Erro de execução |
| qualquer | erro | Erro de execução |

Isso muda o default discutido no discovery, de escolher a variante para rodar as duas: uma variante isolada não permite separar as causas.

Subprocesso evita o cache de módulos e o estado do `pytest` dentro do Streamlit.

### 6. Modelo e validação

`ModeloMBT` ganha `finais: list[str] = []`. As novas regras entram em `validar_coerencia`, que recebe `catalogo` opcional. A checagem de numeração fica em `Requisicao`, retornando 422 antes do LLM. `validar_resposta` continua aceitando `criterios=""` para os testes existentes.

O nome de estado usa o padrão `^[^\W\d_]\w*$`, que permite acentos, confirmados no parser, e rejeita espaço e hífen.

### 7. Timeouts

`TIMEOUT_SEGUNDOS` passa a vir de `QA_TIMEOUT_LLM`, com padrão 180. O front calcula sua espera a partir de `TIMEOUT_SEGUNDOS * MAX_TENTATIVAS` mais uma margem de 10s, importando os valores em vez de duplicá-los. `OLLAMA_MODEL` passa a ter padrão `llama3.1:8b`, em `llm.py` e `.env.example`.

### 8. Demonstração

`EXEMPLOS` deixa de guardar `modelo`, `gherkin` e `pytest`, e cada entrada aponta para um sistema exemplo. O resultado da demonstração sai do mesmo `gerar_*`, a partir do modelo de referência. Comparar o texto da tela com o do exemplo basta para exibir o aviso de edição.

## Risks / Trade-offs

- [Modelo logicamente errado passa na validação] → Mitigado pelo veredito "Modelo diverge do sistema", que é o resultado esperado nesse caso, não uma falha da ferramenta.
- [Catálogo reduz o mérito da extração, pois o LLM recebe os nomes] → Aceito para garantir testes executáveis; a extração livre continua disponível no modo sem sistema.
- [Geração lenta ou timeouts no Ollama] → Timeout maior e configurável. Uma tarefa mede o resultado real antes de concluir. Uma chamada cancelada pelo cliente pode manter o Ollama ocupado e afetar a seguinte.
- [Regras novas de validação aumentam o número de retries] → O limite de 3 tentativas fica mantido; o erro informa o motivo à pessoa, e o modo demonstração segue disponível.
- [Script baixado depende de `sistemas_exemplo`] → O cabeçalho do script traz o comando exato para rodar a partir da raiz do projeto.
- [Saída de falha do `pytest-bdd` muda entre versões] → Só o JUnit XML é usado, e um teste de ponta a ponta cobre o veredito.

## Medição do fluxo real (tarefa 3.3)

Execução em 2026-11-01, com `llama3.1:8b`, catálogo no prompt e timeout de 180s por chamada, em máquina com AMD RX 580 e 15,9 GB de RAM.

| Sistema | Rodada | Concluiu | Duração | Tentativas | Resultado |
|---|---|---|---|---|---|
| Login | 1 | Não | 154s | 1 | Falta de memória ao alocar buffer Vulkan |
| Login | 2 | Não | 183s | 1 | Timeout |
| Login | 3 | Não | 182s | 1 | Timeout |
| Saque | 1 | Não | 181s | 2 | Servidor desconectou na segunda tentativa |
| Saque | 2 | Não | 4s | 1 | Servidor indisponível |
| Saque | 3 | Não | 4s | 1 | Servidor indisponível |

Nenhuma rodada produziu um modelo. As falhas vieram do ambiente: o modelo não coube na memória da GPU, e o log do Ollama mostra que ele reiniciou às 16:27 sem VRAM detectada, em modo CPU. Depois disso, o servidor não voltou a responder.

A medição foi repetida com `gemini-3.8-flash`, pois a API informou que `gemini-2.5-flash` não está mais disponível para novos usuários. O padrão do projeto foi atualizado por isso, ajuste não previsto nas specs.

| Sistema | Rodada | Concluiu | Duração | Tentativas | Veredito | Diferença para a referência |
|---|---|---|---|---|---|---|
| Login | 1 | Não | 180s | 1 | - | Erro 504 do serviço |
| Login | 2 | Sim | 122s | 1 | Bug detectado | Sem o laço em `ContaBloqueada` |
| Login | 3 | Sim | 56s | 1 | Bug detectado | Sem o laço em `ContaBloqueada` |
| Saque | 1 | Sim | 108s | 1 | Bug detectado | Nenhuma |
| Saque | 2 | Sim | 96s | 1 | Bug detectado | Nenhuma |
| Saque | 3 | Sim | 101s | 1 | Bug detectado | Nenhuma |

Com catálogo, 5 de 6 rodadas concluíram, sempre na primeira tentativa, e os 5 modelos passaram em todos os cenários da variante correta. A latência é alta, e o timeout de 180s já causou uma falha. A amostra é pequena, e o Ollama segue sem resultado nesta máquina.

Na verificação em navegador (tarefa 6.7), o fluxo real de Login pela interface falhou uma vez com o mesmo erro 504, exibido corretamente na tela, e concluiu na tentativa seguinte em 115s, com veredito "Bug detectado". Erros do LLM não são repetidos pelo retry, que cobre só modelos inválidos.

## Migration Plan

Sem dados nem deploy para migrar. Clientes de `POST /gerar` precisam numerar os critérios; o único cliente é o front, cujos exemplos já são numerados. Para reverter, basta desfazer o merge.
