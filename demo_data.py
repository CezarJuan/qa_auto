"""Exemplos da barra lateral.

Os que têm sistema exemplo usam o modelo de referência do sistema; os demais, o gabarito de `exemplos/`.
Ambos podem ser exibidos no modo demonstração, sem LLM.
"""
import exemplos
from sistemas_exemplo import SISTEMAS

EXEMPLOS = {
    definicao.nome: {
        "sistema": sistema_id,
        "gabarito": None,
        "user_story": definicao.user_story,
        "criterios": definicao.criterios,
    }
    for sistema_id, definicao in SISTEMAS.items()
}

# Saque ATM fica fora da barra lateral até virar sistema exemplo (add-test-execution),
# para não competir com o sistema exemplo Saque.
for _gabarito_id in ("cupom-promocional", "mfa-bloqueio", "carrinho"):
    _g = exemplos.carregar(_gabarito_id)
    EXEMPLOS[_g["nome"]] = {
        "sistema": None,
        "gabarito": _gabarito_id,
        "user_story": _g["historia"],
        "criterios": _g["criterios"],
    }


def modelo_de_referencia(nome_exemplo: str) -> dict | None:
    """Modelo exibido na demonstração: referência do sistema exemplo ou gabarito; None se não houver."""
    exemplo = EXEMPLOS[nome_exemplo]
    if exemplo["sistema"]:
        return SISTEMAS[exemplo["sistema"]].modelo
    if exemplo["gabarito"]:
        return exemplos.carregar(exemplo["gabarito"])["modelo"]
    return None
