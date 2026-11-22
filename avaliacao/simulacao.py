"""Simulação de um modelo de estados: aplica eventos com dados e informa o estado final e as recusas."""
from dataclasses import dataclass, field

from backend import expressoes
from backend.expressoes import ErroExpressao
from backend.schemas import estado_inicial


class ErroSimulacao(Exception):
    """O modelo não pode ser simulado com os valores informados (ex.: variável sem valor)."""


@dataclass
class Passo:
    evento: str
    aceito: bool
    estado: str


@dataclass
class Simulacao:
    estado: str
    passos: list[Passo] = field(default_factory=list)

    @property
    def ultimo_recusado(self) -> bool:
        return bool(self.passos) and not self.passos[-1].aceito


def simular(modelo: dict, eventos: list[tuple[str, dict]], contexto: dict | None = None) -> Simulacao:
    """Executa os eventos a partir do estado inicial.

    Um evento é recusado quando nenhuma transição do estado atual com esse evento tem guarda verdadeira;
    nesse caso o estado não muda. Com mais de uma transição possível, vale a primeira declarada (num
    modelo válido as guardas não se sobrepõem).
    """
    variaveis = {v["nome"]: v for v in modelo.get("variaveis", [])}
    valores = {nome: v["valor_inicial"] for nome, v in variaveis.items() if v["categoria"] == "estado"}
    valores.update(contexto or {})
    atual = estado_inicial(modelo)
    resultado = Simulacao(atual)
    for evento, dados in eventos:
        ambiente = {**valores, **(dados or {})}
        escolhida = None
        for t in modelo["transicoes"]:
            if t["de"] != atual or t["evento"] != evento:
                continue
            try:
                if expressoes.avaliar_guarda(t.get("guarda"), ambiente):
                    escolhida = t
                    break
            except ErroExpressao as e:
                raise ErroSimulacao(f"Guarda de {t.get('id', '?')} sem como avaliar: {e}") from e
            except (TypeError, ArithmeticError) as e:
                raise ErroSimulacao(f"Guarda de {t.get('id', '?')} falhou: {e}") from e
        if escolhida is None:
            resultado.passos.append(Passo(evento, False, atual))
            continue
        try:
            novos = expressoes.executar_acoes(escolhida.get("acoes") or [], ambiente)
        except (ErroExpressao, KeyError, TypeError, ArithmeticError) as e:
            raise ErroSimulacao(f"Ações de {escolhida.get('id', '?')} falharam: {e}") from e
        # Só estado e contexto persistem: dados de entrada valem apenas para o evento em que chegaram
        valores = {k: novos[k] for k in valores}
        atual = escolhida["para"]
        resultado.passos.append(Passo(evento, True, atual))
    resultado.estado = atual
    return resultado
