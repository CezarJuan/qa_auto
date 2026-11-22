# Tasks

## 1. Provedor e configuração

- [x] 1.1 Atualizar `.env.example` com `OLLAMA_MODEL=llama3.1:8b`, `GEMINI_MODEL`, `QA_TIMEOUT_LLM`, `QA_ORCAMENTO_GERACAO` e `QA_OLLAMA_KEEP_ALIVE`; verificar que o app sobe apenas copiando o arquivo para `.env`
- [x] 1.2 Remover o `except TypeError` de `backend/servico.py` e ajustar os fakes dos testes para a assinatura real; teste confirma uma única chamada ao provedor quando ele lança `TypeError`
- [x] 1.3 Verificar o modelo do Ollama com `ollama.list()` no startup e em `/saude`; testes com fake sem o modelo, com o modelo e com servidor desligado
- [x] 1.4 Implementar o aquecimento com `keep_alive` e o estado em `/saude`; teste com fake verifica a chamada de aquecimento e o estado "carregando modelo"

## 2. API e tratamento de erros

- [x] 2.1 Criar handlers que devolvem `{codigo, mensagem}` para 422, 502, 504 e 500; um teste por código, incluindo erro de validação do Pydantic
- [x] 2.2 Implementar o orçamento total no retry, com `ErroOrcamento` → 504; teste com fake lento confirma 504 sem iniciar tentativa fora do orçamento
- [x] 2.3 Devolver tentativas e duração em `/gerar` e ajustar o front para o novo corpo; teste de contrato do `/gerar`
- [x] 2.4 Front usa `espera_maxima()` baseada no orçamento e trata corpo não JSON e backend desligado; testes com `AppTest` e respostas simuladas

## 3. Entrada de requisitos

- [x] 3.1 Implementar a numeração de critérios e mostrar a lista numerada antes do envio; testes unitários com e sem números e com numeração parcial
- [x] 3.2 Reescrever a importação com marcadores `# História` / `# Critérios`; testes com critério contendo "cada" (bug 2) e arquivo sem história
- [x] 3.3 Importar o arquivo só quando ele muda, para que a edição manual prevaleça (bug 1); teste com `AppTest` importa, edita e confere o texto enviado
- [x] 3.4 Bloquear envio com campo vazio ou acima de 2000 caracteres, com mensagem; testes com `AppTest`
- [x] 3.5 Adicionar os exemplos Cupom, MFA e Carrinho em `demo_data.py`, com critérios numerados; teste carrega cada exemplo sem disparar geração

## 4. Diagrama

- [x] 4.1 Escapar o texto dos eventos e incluir `CA<n>` nos rótulos; testes com evento contendo `:` e aspas e com transição sem critério
- [x] 4.2 Exibir o código Mermaid copiável na aba do diagrama; teste com `AppTest`; teste com `mmdc` pulado quando ele não está instalado

## 5. Modo demonstração

- [x] 5.1 Mostrar o aviso "Demonstração: modelo de referência, sem LLM" em todas as abas; teste com `AppTest`
- [x] 5.2 Recusar texto livre, exemplo editado e exemplo sem modelo de referência (bug 8); testes com requisito de boleto, Login editado e Cupom

## 6. Documentação e integração

- [x] 6.1 Corrigir o README: exemplos reais, escolha de provedor, variáveis de tempo e formato de importação; conferir que cada comando do README funciona
- [x] 6.2 Rodar os 5 exemplos no fluxo real (Ollama e, se disponível, Gemini) e registrar tempo, tentativas e erros em `docs/medicoes/stabilize-pipeline.md`; nenhum erro sem tratamento na interface

## Workflow follow-up

- Rodar `/opsx:verify` e arquivar este change antes de iniciar `fsm-model-v2`.
