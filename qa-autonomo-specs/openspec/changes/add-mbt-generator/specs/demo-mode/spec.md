# Spec Delta

## REMOVED Requirements

### Requirement: Artefatos de teste fora da demo
**Reason**: A geração real de Gherkin e pytest passa a existir neste change.
**Migration**: As abas Gherkin e Pytest seguem `artifact-export`. Os fixtures da demo passam a incluir os artefatos gerados pelo próprio gerador a partir dos gabaritos.
