"""Linha de comando da avaliação.

python -m avaliacao executar --provedor ollama --modelo llama3.1:8b --rodadas 3 --conjunto teste
python -m avaliacao executar --provedor gemini --modelo gemini-3.8-flash --casos saque-atm,mfa-bloqueio
python -m avaliacao comparar resultados/<execucao-a> resultados/<execucao-b> [--saida comparacao.md]
python -m avaliacao casos
"""
import argparse
import sys
from pathlib import Path

from .casos import ErroCaso, carregar_conjunto, verificar_composicao
from .executor import SAIDA_PADRAO, Configuracao, ErroVazamento, comparar, executar


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="python -m avaliacao", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    ex = sub.add_parser("executar", help="Roda a extração contra os casos de referência")
    ex.add_argument("--provedor", choices=["ollama", "gemini"], required=True)
    ex.add_argument("--modelo", required=True, help="Ex.: llama3.1:8b, qwen2.5:7b, gemini-3.8-flash")
    ex.add_argument("--rodadas", type=int, default=3)
    ex.add_argument("--conjunto", choices=["teste", "desenvolvimento", "ambos"], default="teste")
    ex.add_argument("--casos", help="Ids separados por vírgula (subconjunto)")
    ex.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ex.add_argument("--alinhamento-semantico", action="store_true",
                    help="Usa embeddings do Ollama (nomic-embed-text) para nomes sem correspondência")

    cmp_ = sub.add_parser("comparar", help="Compara duas ou mais execuções")
    cmp_.add_argument("execucoes", nargs="+", type=Path)
    cmp_.add_argument("--saida", type=Path, help="Grava a comparação em Markdown")

    sub.add_parser("casos", help="Valida e lista os casos de referência")

    args = parser.parse_args(argv)
    try:
        if args.comando == "executar":
            if args.rodadas < 1:
                parser.error("--rodadas deve ser ao menos 1")
            config = Configuracao(
                provedor=args.provedor, modelo=args.modelo, rodadas=args.rodadas, conjunto=args.conjunto,
                casos=[c.strip() for c in args.casos.split(",")] if args.casos else None,
                alinhamento_semantico=args.alinhamento_semantico,
            )
            pasta = executar(config, saida=args.saida)
            print(f"Resultados em {pasta}")
        elif args.comando == "comparar":
            texto = comparar(args.execucoes)
            print(texto)
            if args.saida:
                args.saida.write_text(texto, encoding="utf-8")
        else:
            casos = carregar_conjunto()
            verificar_composicao(casos)
            for c in casos:
                print(f"{c.id:24} {c.conjunto:16} {c.dominio:12} {len(c.criterios)} critérios, "
                      f"{len(c.propriedades)} propriedades")
            print(f"{len(casos)} casos, {len({c.dominio for c in casos})} domínios: conjunto válido.")
    except (ErroCaso, ErroVazamento, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
