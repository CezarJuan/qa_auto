# Tasks

## 1. Configuração e provedor

- [ ] 1.1 Ajustar `.env.example` com modelo com tag (`llama3.1:8b`), `TEMPO_LIMITE_CHAMADA` e `ORCAMENTO_TOTAL_GERACAO`; verificar que o app sobe só copiando o arquivo
- [ ] 1.2 Verificar disponibilidade do modelo no startup e em `/saude`, listando modelos instalados; teste com fake do Ollama sem o modelo
- [ ] 1.3 Remover o `except TypeError` de `backend/servico.py` e ajustar os fakes para a assinatura real; teste garante uma única chamada ao provedor
- [ ] 1.4 Implementar aquecimento com `keep_alive`; teste verifica a chamada de aquecimento e a interface mostra "carregando modelo"
- [ ] 1.5 Executar o fluxo real com Gemini uma vez e registrar o resultado no README

## 2. API e tratamento de erros

- [ ] 2.1 Padronizar respostas 422/502/504/500 com corpo JSON `{codigo, mensagem}`; testes para cada código
- [ ] 2.2 Implementar orçamento total no retry; teste com fake lento confirma 504 antes do orçamento
- [ ] 2.3 Front usa orçamento + margem e trata corpo não JSON e backend desligado; testes com AppTest

## 3. Entrada de requisitos

- [ ] 3.1 Numerar critérios de 1 a N preservando numeração existente; testes unitários com e sem números
- [ ] 3.2 Reescrever a importação com marcadores `# História` / `# Critérios`; teste com critério contendo "cada" (bug 2)
- [ ] 3.3 Garantir que o texto editado após importação é o enviado (bug 1); teste com AppTest
- [ ] 3.4 Adicionar exemplos Saque ATM, Cupom e MFA à barra lateral, junto de Login e Carrinho; teste carrega cada um sem disparar geração

## 4. Diagrama

- [ ] 4.1 Gerar id ASCII + rótulo original para cada estado e rejeitar colisões (bug 3); testes com "Com itens", "Cartão Retido" e colisão
- [ ] 4.2 Rotular transições com evento e critérios; validar o código gerado com `mmdc` em teste

## 5. Modo demonstração

- [ ] 5.1 Exibir aviso de pré-gravado em todas as abas na demo; teste com AppTest
- [ ] 5.2 Recusar texto livre na demo (bug 8); teste com requisito de boleto
- [ ] 5.3 Esconder download e mostrar "em breve" nas abas Gherkin e Pytest fora da demo (bug 9); teste com AppTest

## 6. Integração

- [ ] 6.1 Rodar os 5 exemplos no fluxo real com Ollama e registrar tempo e tentativas em `docs/`; nenhum erro não tratado na interface
- [ ] 6.2 Corrigir o README (exemplos reais, como configurar provedor e modelo); conferir que cada comando do README funciona

## Workflow follow-up

- Rodar `/opsx:verify` e `/opsx:archive` antes de iniciar `fsm-model-v2`.
