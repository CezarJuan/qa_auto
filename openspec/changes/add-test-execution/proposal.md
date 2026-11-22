# Proposal

## Why

Hoje os testes rodam contra dois sistemas exemplo (Login e Saque), cada um com uma única variante com bug. Isso prova que a ferramenta detecta um defeito, mas não dá a evidência quantitativa que os Resultados Esperados do 5W2H pedem: taxa de defeitos detectados nos 3 exemplos canônicos, cenários de borda, falsos alarmes de modelos extraídos e comparação de tempo e eficácia com testes escritos à mão. O Saque atual também não é o Saque canônico, porque não tem valor, saldo nem múltiplo de 20.

## What Changes

- **BREAKING** Sistemas exemplo para os exemplos canônicos: Saque ATM (substitui o Saque atual, id `saque-atm`), Cupom Promocional, Autenticação MFA e Carrinho, além do Login. Todos usam variáveis de contexto e de entrada quando o gabarito usa.
- **BREAKING** A variante única com bug dá lugar a mutantes documentados, ao menos dois por sistema, cada um com uma única alteração, a descrição do defeito e o critério violado. Os mutantes incluem os erros que o LLM cometeu no explore e ao menos um de fronteira por sistema.
- A execução roda a suíte contra a variante correta e contra todos os mutantes. O veredito passa a mostrar a taxa de mutantes detectados, os sobreviventes e os falsos alarmes.
- Resultado agregado por critério de aceite, usando as tags `@CA-<n>`.
- Execução e análise de mutantes também por linha de comando.
- Comparação com uma suíte escrita à mão para Saque ATM, Cupom e MFA: cenários, bordas, mutantes detectados e tempo de elaboração.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `sistemas-exemplo`: novos sistemas, mutantes no lugar da variante com bug e independência verificável do modelo.
- `execucao-testes`: execução contra mutantes, veredito com taxa de detecção e falsos alarmes, resultado por critério, linha de comando e comparação com suíte manual.

## Impact

- `sistemas_exemplo/`: novos módulos, mutantes e `mutantes.yaml` por sistema. `saque.py` é substituído por `saque_atm.py`.
- `backend/execucao.py`: execução por alvo, agregação por critério, análise de mutantes e comparação.
- `app.py`: aba de execução com taxa de detecção, sobreviventes e falsos alarmes.
- `demo_data.py`: Cupom, MFA e Carrinho passam a ter sistema exemplo.
- `suite_manual/`: suítes escritas pelo grupo, com tempo registrado.
- `docs/resultados/`: tabela final para o relatório da disciplina.
