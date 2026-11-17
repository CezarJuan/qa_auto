# Design

## Context

Ver proposal.md (Why). Depende do formato e do interpretador de guardas e ações de `fsm-model-v2`. O explore observou execuções entre 14 s e 90 s. Na medição do change `gerar-testes-executaveis`, o Ollama não concluiu nenhuma rodada nesta máquina (falta de VRAM), e o Gemini levou de 56 s a 122 s por geração. Por isso a avaliação precisa rodar sem supervisão, registrar a latência e aceitar o Gemini como provedor.

## Goals / Non-Goals

**Goals:**
- Um número por configuração que diga se a extração melhorou, com variância conhecida.
- Detectar exatamente o tipo de erro semântico que o explore encontrou.

**Non-Goals:**
- Avaliar os testes gerados (change 5).
- Medir guardas por equivalência lógica. As propriedades cobrem isso pelo comportamento.

## Decisions

### 1. Formato dos casos: um YAML por caso

Os gabaritos vêm dos arquivos de `exemplos/` criados em `fsm-model-v2` (`saque-atm`, `cupom-promocional`, `mfa-bloqueio`, `carrinho`) e do modelo de referência do sistema exemplo Login. O caso `login` usa a contagem desdobrada em estados, o que também mede se o LLM segue esse estilo quando o catálogo pede.

```yaml
id: saque-atm
dominio: bancario
conjunto: teste
historia: "Como cliente, quero sacar dinheiro no caixa eletrônico para ..."
criterios:
  1: "O cliente deve inserir o cartão e informar o PIN"
  2: "O saque só é permitido se o valor for menor ou igual ao saldo"
  3: "Após 3 PINs inválidos o cartão é retido"
  4: "O valor deve ser múltiplo de 20 (cédulas disponíveis)"
gabarito: { ... ModeloEstados ... }
sinonimos:
  estados: { AguardandoPin: [AguardandoSenha, InformandoPin] }
  eventos: { pin_invalido: [informar_pin_invalido, senha_incorreta] }
propriedades:
  - criterio: 3
    descricao: "Um PIN errado não retém o cartão"
    eventos: [ {evento: inserir_cartao}, {evento: pin_invalido} ]
    estado_esperado: AguardandoPin
  - criterio: 3
    descricao: "Três PINs errados retêm o cartão"
    eventos: [ {evento: inserir_cartao}, {evento: pin_invalido}, {evento: pin_invalido}, {evento: pin_invalido} ]
    estado_esperado: CartaoRetido
  - criterio: 2
    descricao: "Saque acima do saldo é recusado"
    contexto: { saldo: 100 }
    eventos: [ ..., {evento: solicitar_saque, dados: {valor: 120}} ]
    estado_esperado: SaldoInsuficiente
```

YAML foi escolhido no lugar de JSON porque o grupo vai escrever os casos à mão e o YAML aceita comentários e texto em várias linhas. O critério 4 usa o operador `%`, incluído na linguagem de guardas em `fsm-model-v2`.

### 2. Alinhamento em três passos

1. Normalização: minúsculas, sem acento, sem `_`, sem espaço.
2. Sinônimos do caso.
3. Opcional, com `--alinhamento-semantico`: similaridade de embeddings (`nomic-embed-text` via Ollama) acima de 0,85, atribuição gulosa um-para-um.

O passo 3 fica desligado por padrão, para que as métricas principais sejam determinísticas. Ele serve para revisar sinônimos que faltam.

### 3. Transição considerada correta

Origem, evento e destino precisam estar mapeados e iguais. A guarda não entra nessa métrica; é avaliada pelas propriedades. Isso evita penalizar `valor <= saldo` vs `saldo >= valor`.

### 4. Evento recusado

Na simulação, um evento é recusado se nenhuma transição saindo do estado atual tiver esse evento com guarda verdadeira. O estado permanece o mesmo.

### 5. Saída

`resultados/<AAAAMMDD-HHMM>_<provedor>_<modelo>_<prompt>/` com `rodadas/*.json`, `resumo.csv`, `relatorio.md` e `config.json`. O subcomando `comparar` lê os `resumo.csv`.

## Risks / Trade-offs

- [Escrever 15 gabaritos à mão leva tempo] → Gerar rascunhos com um LLM maior (Gemini) e revisar à mão. O conjunto de teste deve ser revisado pelos dois integrantes.
- [Sinônimos incompletos subestimam a precisão] → O relatório lista os elementos não mapeados para revisão. O alinhamento semântico ajuda a encontrá-los.
- [Avaliação longa em hardware modesto] → `--casos` permite rodar um subconjunto; a duração estimada aparece antes de começar.
