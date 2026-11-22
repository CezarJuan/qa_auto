# Design

## Context

Ver proposal.md (Why). No cronograma do 5W2H esta é a Semana 2. Aqui ela vem por último porque grava os objetos definidos pelos changes 2, 4 e 5. Se o grupo precisar da persistência mais cedo, dá para aplicá-la logo após `add-mbt-generator`: basta mover o requisito de execuções e a TB_EXECUCAO para `add-test-execution`.

## Goals / Non-Goals

**Goals:**
- Histórico consultável e reabertura offline, como pede o cenário BCS.

**Non-Goals:**
- Multiusuário, autenticação ou banco em servidor.
- Busca textual no histórico.

## Decisions

### 1. Modelo relacional

```
TB_PROJETO (id, nome UNIQUE, criado_em)
TB_USER_STORY (id, projeto_id FK, papel, acao, beneficio, texto_completo, criado_em)
TB_CRITERIO_ACEITE (id, user_story_id FK, numero, texto, UNIQUE(user_story_id, numero))
TB_MODELO_ESTADOS (id, user_story_id FK, modelo_json, mermaid, provedor, modelo_llm,
                   versao_prompt, tentativas_json, duracao_ms, situacao, erros_json, criado_em)
TB_SUITE_TESTE (id, modelo_estados_id FK, estrategia, bordas BOOL, cobertura_json,
                feature, teste_py, adaptador_py, criado_em)
TB_EXECUCAO (id, suite_teste_id FK, sistema, veredito, resultado_json, mutantes_json, duracao_ms, criado_em)
```

As FKs usam `ON DELETE CASCADE`, e o SQLite precisa de `PRAGMA foreign_keys=ON` em cada conexão (evento `connect` do SQLAlchemy). O modelo, as tentativas, a cobertura e os resultados ficam em colunas JSON (TEXT): são lidos inteiros e nunca filtrados por campo interno.

### 2. Alembic chamado pelo `init_db.py`

`init_db.py` cria o diretório, roda `alembic upgrade head` e insere o projeto "Geral" se não existir. Isso atende aos "scripts de migração automática" do 5W2H e permite evoluir o esquema. Alternativa: só `metadata.create_all()`. É mais simples, mas não atualiza tabelas existentes, então foi descartada.

### 3. SQLAlchemy 2.0 com camada de repositório

Classes ORM em `database/modelos.py` e funções de repositório (`registrar_geracao`, `listar_geracoes`, ...) em `database/repositorio.py`. A interface e a API usam só o repositório. Nos testes, o repositório usa SQLite em memória.

### 4. Gravação onde a ação acontece

A extração roda na API, então `/gerar` grava a geração (com sucesso ou falha) na mesma requisição e devolve o id dela. A geração de artefatos e a execução rodam no processo do front e da linha de comando, como definido no change arquivado `gerar-testes-executaveis`. Por isso, a suíte e a execução são gravadas ali, pelo mesmo repositório, ligadas ao id da geração. O material original previa gravar tudo na API, mas isso exigiria mover a execução para o backend. A gravação não pode derrubar a operação: se falhar, o resultado sai normalmente com um aviso, e o erro vai para o log.

Gerações do modo demonstração não são gravadas, porque não chamam o LLM e sempre reproduzem o modelo de referência.

## Risks / Trade-offs

- [JSON em colunas impede consultas finas] → Aceitável no escopo. Se precisar, cria-se uma view ou se extraem colunas em migração futura.
- [Arquivo `.db` versionado por engano] → Adicionar `database/*.db` ao `.gitignore` na primeira tarefa.
