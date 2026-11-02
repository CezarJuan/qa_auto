"""Prompts da extração do modelo de estados, versionados por arquivo."""
import json
import re
from pathlib import Path

from sistemas_exemplo import Catalogo

PASTA = Path(__file__).resolve().parent
VERSAO_PROMPT = "extracao-v2"
SYSTEM_PROMPT = (PASTA / "extracao_v2.md").read_text(encoding="utf-8")

# Casos do benchmark usados como exemplo em cada versão do prompt. A avaliação recusa uma configuração
# cujo prompt use um caso do conjunto de teste.
EXEMPLOS_DO_PROMPT: dict[str, list[str]] = {"extracao-v2": ["login"]}


def exemplo_resolvido() -> dict:
    """Modelo do exemplo resolvido embutido no prompt (validado nos testes)."""
    bloco = re.search(r"```json\n(.*?)\n```", SYSTEM_PROMPT, flags=re.DOTALL)
    return json.loads(bloco.group(1))


def _secao_catalogo(catalogo: Catalogo) -> str:
    estados = "\n".join(f"- {nome}: {desc}" for nome, desc in catalogo.estados.items())
    eventos = "\n".join(f"- {nome}: {desc}" for nome, desc in catalogo.eventos.items())
    if catalogo.variaveis:
        variaveis = "Variáveis:\n" + "\n".join(f"- {nome}: {desc}" for nome, desc in catalogo.variaveis.items())
    else:
        variaveis = (
            "Variáveis: nenhuma. Não declare variáveis; represente cada etapa de uma contagem "
            "com um estado próprio do catálogo."
        )
    return (
        "\n\nCatálogo do sistema (use SOMENTE estes ids e nomes, exatamente como escritos):\n"
        f"Estado inicial: {catalogo.inicial}\n"
        f"Estados:\n{estados}\n"
        f"Eventos:\n{eventos}\n"
        f"{variaveis}"
    )


def montar_user_prompt(user_story: str, criterios: str, catalogo: Catalogo | None = None) -> str:
    prompt = f"História de usuário:\n{user_story}\n\nCritérios de aceite:\n{criterios}"
    return prompt + _secao_catalogo(catalogo) if catalogo else prompt


def montar_prompt_correcao(erros: list) -> str:
    """Pede a correção do modelo anterior (a mensagem logo acima), com todos os erros agrupados."""
    linhas = "\n".join(f"- [{e.codigo}] {e.mensagem}" for e in erros) if erros else "- resposta inválida"
    return (
        "O modelo que você enviou acima não passou na validação. Erros encontrados, do mais estrutural "
        f"ao mais fino:\n{linhas}\n\n"
        "Corrija TODOS os erros partindo do modelo anterior, mantendo o que já estava certo, e responda "
        "novamente SOMENTE com o JSON completo."
    )
