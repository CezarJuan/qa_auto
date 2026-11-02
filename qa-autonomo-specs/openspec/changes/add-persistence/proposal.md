# Proposal

## Why

O 5W2H prevê uma camada relacional em SQLite com SQLAlchemy e migração automática para registrar projetos, requisitos, modelos e suítes, e o cenário BCS exige o histórico completo das consultas. Hoje `database/` está vazio e nada do que é gerado é guardado.

## What Changes

- Banco SQLite com as tabelas do 5W2H (TB_PROJETO, TB_USER_STORY, TB_CRITERIO_ACEITE, TB_MODELO_ESTADOS, TB_SUITE_TESTE) e TB_EXECUCAO para os resultados de `add-test-execution`.
- Script `init_db.py` que cria e atualiza o esquema de forma idempotente, com versionamento.
- Registro automático de cada geração (inclusive as que falharam) e de cada execução.
- Histórico na interface: listar por projeto, reabrir uma geração sem chamar o LLM e excluir projeto.

## Capabilities

### New Capabilities
- `generation-history`: persistência de projetos, requisitos, modelos, suítes e execuções, e consulta ao histórico.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- `database/` (modelos ORM, migrações, `init_db.py`), `app.py` (seletor de projeto e aba Histórico), backend (gravação após geração e execução).
- Novas dependências: `sqlalchemy` e `alembic`.
- O arquivo `.db` não entra no git.
