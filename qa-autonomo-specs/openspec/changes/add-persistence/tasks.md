# Tasks

## 1. Esquema e migração

- [ ] 1.1 Adicionar `sqlalchemy` e `alembic`, configurar o Alembic em `database/` e incluir `database/*.db` no `.gitignore`; `alembic --help` roda no ambiente
- [ ] 1.2 Criar as classes ORM das 6 tabelas com FKs em cascata e `PRAGMA foreign_keys=ON`; teste de exclusão em cascata em memória
- [ ] 1.3 Gerar a migração inicial e o `init_db.py` com projeto "Geral"; teste roda o script duas vezes e confere tabelas e dados

## 2. Repositório

- [ ] 2.1 Implementar registro de geração (sucesso e falha) com critérios; testes dos dois cenários
- [ ] 2.2 Implementar registro de suíte e de execução; teste com execução contra mutante
- [ ] 2.3 Implementar listagem por projeto, leitura de geração completa e exclusão de projeto; testes de ordem e cascata

## 3. Integração

- [ ] 3.1 Gravar após geração e execução na API, sem derrubar a resposta se a gravação falhar; teste com repositório que lança erro
- [ ] 3.2 Seletor e criação de projeto na interface, com "Geral" como padrão; teste com AppTest
- [ ] 3.3 Aba Histórico com reabertura offline e exclusão com confirmação; teste com AppTest e provedor desligado
- [ ] 3.4 Documentar `init_db.py` e o modelo relacional (DER) no README
