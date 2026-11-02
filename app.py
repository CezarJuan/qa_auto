import hashlib
import html
import os
import re
import time

import requests
import streamlit as st

from backend.entrada import (
    ErroImportacao,
    extrair_requisitos_de_texto,
    numerar_criterios,
    total_criterios,
    validar_entrada,
)
from backend.execucao import (
    BUG_DETECTADO,
    BUG_NAO_DETECTADO,
    ERRO_EXECUCAO,
    MODELO_DIVERGE,
    Execucao,
    ResultadoVariante,
    executar_testes,
)
from backend.geracao import gerar_artefatos, modelo_para_mermaid
from backend.schemas import MAX_CARACTERES, criterios_cobertos, estado_inicial
from backend.servico import espera_maxima
from demo_data import EXEMPLOS, modelo_de_referencia
from sistemas_exemplo import SISTEMAS

API_URL = os.getenv("QA_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="QA Autonomous",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- estilo claro (Light Mode)
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 0% -10%, rgba(99, 102, 241, 0.08), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, rgba(14, 165, 233, 0.08), transparent 50%),
        #f8fafc;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1400px; }

/* ---------- hero ---------- */
.hero {
    padding: 28px 32px; border-radius: 20px; margin-bottom: 24px;
    background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
    animation: fadeUp .5s ease both;
}
.hero h1 {
    margin: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -.02em;
    background: linear-gradient(90deg, #4338ca, #0284c7);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 6px 0 0; color: #475569; font-size: 1.02rem; }
.stepper { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.step {
    padding: 6px 14px; border-radius: 999px; font-size: .82rem; font-weight: 600;
    background: #eef2ff; border: 1px solid #c7d2fe; color: #3730a3;
}
.step b { color: #4f46e5; margin-right: 6px; }

/* ---------- cards & cabeçalhos ---------- */
.card-title {
    font-size: 1.05rem; font-weight: 700; color: #0f172a; margin: 4px 0 10px;
    display: flex; align-items: center; gap: 8px;
}
.badge {
    font-size: .72rem; padding: 2px 10px; border-radius: 999px; font-weight: 700;
    background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe;
}
.badge.demo { background: #fef9c3; color: #854d0e; border-color: #fde047; }
.badge.live { background: #dcfce7; color: #166534; border-color: #86efac; }
.badge.time { background: #f1f5f9; color: #334155; border-color: #cbd5e1; }

[data-testid="stTextArea"] textarea {
    background: #ffffff !important; border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important; color: #0f172a !important; line-height: 1.55;
    box-shadow: 0 1px 2px rgba(0,0,0,.03);
    transition: border-color .15s, box-shadow .15s;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
}
[data-testid="stTextArea"] label p { font-weight: 600; color: #1e293b; }

/* ---------- botões ---------- */
.stButton > button[kind="primary"], .stDownloadButton > button {
    border: 0; border-radius: 12px; font-weight: 700; padding: .7rem 1.2rem;
    background: linear-gradient(90deg, #4f46e5, #0284c7); color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.28);
    transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px); filter: brightness(1.05);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.38); color: #ffffff !important;
}

/* ---------- métricas ---------- */
.metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 6px 0 18px; }
.metric {
    padding: 14px 16px; border-radius: 14px; animation: fadeUp .4s ease both;
    background: #ffffff; border: 1px solid #e2e8f0;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
}
.metric .v { font-size: 1.75rem; font-weight: 800; color: #0f172a; line-height: 1.15; }
.metric .l { font-size: .74rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; margin-top: 4px; font-weight: 600; }
.metric.ok .v { color: #16a34a; }
.metric.warn .v { color: #d97706; }
.metric.info .v { color: #2563eb; }

/* ---------- abas ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 2px solid #e2e8f0; }
.stTabs [data-baseweb="tab"] {
    height: 44px; padding: 0 16px; border-radius: 10px 10px 0 0; font-weight: 600; color: #64748b;
}
.stTabs [aria-selected="true"] { color: #4338ca !important; background: #eef2ff; }
.stTabs [data-baseweb="tab-highlight"] { background: #4f46e5; height: 3px; }

/* ---------- estado vazio ---------- */
.empty {
    text-align: center; padding: 60px 20px; border-radius: 18px;
    background: #ffffff; border: 2px dashed #cbd5e1; color: #64748b; animation: fadeUp .5s ease both;
}
.empty .icon { font-size: 3rem; animation: float 3s ease-in-out infinite; }
.empty h3 { color: #0f172a; margin: 10px 0 4px; font-weight: 700; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}
.about {
    padding: 14px 16px; border-radius: 12px; font-size: .85rem; color: #475569; line-height: 1.6;
    background: #f8fafc; border: 1px solid #e2e8f0;
}
.about b { color: #0f172a; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@media (max-width: 1000px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- lógica
AVISO_DEMO = "Demonstração: modelo de referência, sem LLM"
MENSAGENS_STATUS = {
    422: "Requisição inválida",
    500: "Erro interno no servidor",
    502: "Falha no provedor de LLM",
    504: "Tempo esgotado no servidor",
}


def mensagem_de_erro(resp) -> str:
    """Mensagem legível para qualquer resposta de erro, com ou sem corpo JSON."""
    try:
        corpo = resp.json()
    except ValueError:
        corpo = None
    mensagem = None
    if isinstance(corpo, dict):
        mensagem = corpo.get("mensagem") or corpo.get("detail")
        if isinstance(mensagem, list):
            mensagem = "; ".join(str(d.get("msg", d)) for d in mensagem)
    if not mensagem:
        mensagem = MENSAGENS_STATUS.get(resp.status_code, "Erro no servidor")
    return f"{mensagem} (status {resp.status_code})"


def chamar_backend(
    user_story: str,
    criterios: str,
    motor: str,
    api_key: str | None = None,
    sistema: str | None = None,
) -> dict:
    """Envia os requisitos ao backend e devolve o corpo da resposta.

    Lança RuntimeError com mensagem legível em qualquer falha, sem expor exceções ao usuário.
    """
    payload = {"user_story": user_story, "criterios": criterios, "motor": motor, "sistema": sistema}
    if api_key:
        payload["api_key"] = api_key
    try:
        resp = requests.post(f"{API_URL}/gerar", json=payload, timeout=espera_maxima())
    except requests.ConnectionError:
        raise RuntimeError(
            "O backend está indisponível. Inicie-o com: `uvicorn backend.main:app --reload` "
            "ou ative o **Modo demonstração** na barra lateral."
        )
    except requests.Timeout:
        raise RuntimeError(f"O backend não respondeu em {espera_maxima()}s.")
    except requests.RequestException as e:
        raise RuntimeError(f"Falha na comunicação com o backend: {e}")
    if resp.status_code != 200:
        raise RuntimeError(mensagem_de_erro(resp))
    try:
        corpo = resp.json()
        corpo["modelo"]
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("O backend devolveu uma resposta em formato inesperado.")
    return corpo


def motivo_recusa_demo(nome_exemplo: str, user_story: str, criterios: str) -> str | None:
    """Na demonstração, só exemplos com modelo de referência e sem edição podem ser exibidos."""
    exemplo = EXEMPLOS[nome_exemplo]
    if (user_story.strip(), criterios.strip()) != (exemplo["user_story"].strip(), exemplo["criterios"].strip()):
        return (
            f"O texto na tela não corresponde ao exemplo “{nome_exemplo}”: ele foi editado ou digitado. "
            "A demonstração só exibe exemplos sem edição. "
            "Desative o **Modo demonstração** para processar texto livre."
        )
    if modelo_de_referencia(nome_exemplo) is None:
        return (
            f"O exemplo “{nome_exemplo}” ainda não tem modelo de referência, então não pode ser exibido "
            "na demonstração. Desative o **Modo demonstração** para gerá-lo com o LLM."
        )
    return None


def importar_arquivo(arquivo) -> None:
    """Preenche os campos só quando o arquivo muda, para que edições posteriores prevaleçam."""
    if arquivo is None:
        st.session_state.pop("arquivo_importado", None)
        st.session_state.pop("importacao", None)
        return
    dados = arquivo.getvalue()
    assinatura = f"{arquivo.name}:{hashlib.sha256(dados).hexdigest()}"
    if st.session_state.get("arquivo_importado") == assinatura:
        return
    st.session_state["arquivo_importado"] = assinatura
    try:
        historia, criterios_importados = extrair_requisitos_de_texto(dados.decode("utf-8-sig"))
    except UnicodeDecodeError:
        st.session_state["importacao"] = ("erro", "O arquivo precisa estar em UTF-8.")
        return
    except ErroImportacao as e:
        st.session_state["importacao"] = ("erro", str(e))
        return
    st.session_state["user_story"] = historia
    st.session_state["criterios"] = criterios_importados
    st.session_state.pop("resultado", None)
    st.session_state.pop("execucao", None)
    st.session_state["importacao"] = ("ok", f"Requisitos importados de {arquivo.name}.")


def render_mermaid(mermaid_code: str):
    """Renderiza código Mermaid (tema claro) via HTML + Javascript em iframe isolado."""
    html_code = f"""
    <style>
      body {{ margin: 0; background: transparent; }}
      .box {{ display: flex; justify-content: center; padding: 20px;
              background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0;
              box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    </style>
    <div class="box"><div class="mermaid">{html.escape(mermaid_code)}</div></div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#e0e7ff',
                primaryTextColor: '#1e1b4b',
                primaryBorderColor: '#6366f1',
                lineColor: '#0284c7',
                fontFamily: 'Inter, sans-serif'
            }}
        }});
    </script>
    """
    st.iframe(html_code, height=540)


RESULTADO_TENTATIVA = {"valido": "✅ Válido", "invalido": "❌ Inválido", "timeout": "⏱️ Timeout"}
CATEGORIA_VARIAVEL = {"estado": "Estado (muda por ações)", "entrada": "Entrada (vem com o evento)",
                      "contexto": "Contexto (fixa no cenário)"}


def render_analise(modelo: dict, historico: list[dict]):
    """Análise do LLM, variáveis do modelo e tentativas da extração."""
    st.markdown("**Análise dos critérios**")
    st.write(modelo.get("analise") or "—")
    st.markdown("**Variáveis**")
    if modelo.get("variaveis"):
        st.dataframe(
            [
                {"Nome": v["nome"], "Tipo": v["tipo"], "Categoria": CATEGORIA_VARIAVEL.get(v["categoria"], v["categoria"]),
                 "Valor inicial": "—" if v.get("valor_inicial") is None else str(v["valor_inicial"])}
                for v in modelo["variaveis"]
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("O modelo não declara variáveis: contagens são representadas por estados.")
    if historico:
        st.markdown("**Tentativas da extração**")
        st.dataframe(
            [
                {"Tentativa": i, "Resultado": RESULTADO_TENTATIVA.get(t["resultado"], t["resultado"]),
                 "Duração": f"{t['duracao']:.1f}s", "Erros": t.get("erro") or "—"}
                for i, t in enumerate(historico, start=1)
            ],
            width="stretch",
            hide_index=True,
        )


def nome_sistema(sistema_id: str) -> str:
    return SISTEMAS[sistema_id].nome if sistema_id else "Nenhum (gerar só esqueleto)"


def carregar_exemplo():
    ex = EXEMPLOS[st.session_state["exemplo"]]
    st.session_state["user_story"] = ex["user_story"]
    st.session_state["criterios"] = ex["criterios"]
    st.session_state["sistema_alvo"] = ex["sistema"] or ""
    st.session_state.pop("resultado", None)
    st.session_state.pop("execucao", None)


def tabela_cenarios(resultado: ResultadoVariante) -> list[dict]:
    return [
        {"Cenário": c.nome, "Resultado": "✅ Passou" if c.passou else "❌ Falhou"}
        for c in resultado.cenarios
    ]


def render_falhas(titulo: str, resultado: ResultadoVariante):
    if resultado.falhas:
        linhas = [f"- **{c.nome}:** {c.motivo}" for c in resultado.falhas]
        st.markdown(f"**Falhas no {titulo}**\n" + "\n".join(linhas))


def render_execucao(execucao: Execucao):
    if execucao.veredito == ERRO_EXECUCAO:
        motivo = execucao.correto.erro or execucao.bug.erro
        st.error(f"**{ERRO_EXECUCAO}:** {motivo}", icon="🚨")
        return
    if execucao.veredito == BUG_DETECTADO:
        st.success(f"**{BUG_DETECTADO}:** os testes passam no sistema correto e falham no sistema com bug.")
    elif execucao.veredito == BUG_NAO_DETECTADO:
        st.warning(f"**{BUG_NAO_DETECTADO}:** os testes passam nas duas variantes, então são insuficientes.")
    elif execucao.veredito == MODELO_DIVERGE:
        st.warning(f"**{MODELO_DIVERGE}:** há testes falhando no sistema correto. Revise o modelo gerado.")

    col_correto, col_bug = st.columns(2)
    with col_correto:
        st.markdown("**Sistema correto**")
        st.dataframe(tabela_cenarios(execucao.correto), width="stretch", hide_index=True)
    with col_bug:
        st.markdown("**Sistema com bug**")
        if execucao.bug.erro:
            st.caption(f"Sem resultado: {execucao.bug.erro}")
        else:
            st.dataframe(tabela_cenarios(execucao.bug), width="stretch", hide_index=True)
    render_falhas("sistema correto", execucao.correto)
    render_falhas("sistema com bug", execucao.bug)


# estado inicial
if "user_story" not in st.session_state:
    nome0 = next(iter(EXEMPLOS))
    st.session_state["exemplo"] = nome0
    st.session_state["user_story"] = EXEMPLOS[nome0]["user_story"]
    st.session_state["criterios"] = EXEMPLOS[nome0]["criterios"]
    st.session_state["sistema_alvo"] = EXEMPLOS[nome0]["sistema"] or ""

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    modelo_selecionado = st.selectbox("Motor LLM", ["Gemini (Cloud)", "Ollama (Local)"])

    api_key_custom = None
    if modelo_selecionado == "Gemini (Cloud)":
        api_key_custom = st.text_input(
            "🔑 Chave API Gemini (opcional)",
            type="password",
            placeholder="AIzaSy...",
            help="Se preenchida, substitui temporariamente a GEMINI_API_KEY do arquivo .env.",
        )

    modo_demo = st.toggle(
        "Modo demonstração",
        value=True,
        help="Usa dados de exemplo rápidos, sem backend nem LLM. Desative para chamar a API real.",
    )
    st.selectbox("📚 Carregar exemplo", list(EXEMPLOS), key="exemplo", on_change=carregar_exemplo)
    st.selectbox(
        "🎯 Sistema alvo",
        [*SISTEMAS, ""],
        key="sistema_alvo",
        format_func=nome_sistema,
        help="Sistema contra o qual os testes rodam. Sem sistema, os artefatos são apenas esqueletos.",
    )
    st.markdown("---")
    st.markdown(
        '<div class="about"><b>Fatec Cotia</b><br>Processamento de Linguagem Natural<br><br>'
        "<b>Aluno</b><br>Juan Cezar Yghor Andrade</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- hero
st.markdown(
    """
    <div class="hero">
        <h1>🤖 QA Autonomous</h1>
        <p>Geração automática de testes com Processamento de Linguagem Natural e Model-Based Testing.</p>
        <div class="stepper">
            <span class="step"><b>1</b>Requisitos</span>
            <span class="step"><b>2</b>Modelo de estados</span>
            <span class="step"><b>3</b>Cenários BDD</span>
            <span class="step"><b>4</b>Scripts Pytest</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- layout
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    badge = '<span class="badge demo">DEMO</span>' if modo_demo else '<span class="badge live">API REAL</span>'
    st.markdown(f'<div class="card-title">📥 Entradas {badge}</div>', unsafe_allow_html=True)

    # 1. Upload de Arquivos
    with st.expander("📂 Importar arquivo (.txt, .md)", expanded=False):
        st.caption("Use as seções `# História` e `# Critérios`.")
        uploaded_file = st.file_uploader(
            "Selecione um arquivo de requisitos",
            type=["txt", "md"],
            key="arquivo",
            help="Carrega o conteúdo nos campos abaixo. Edições feitas depois prevalecem.",
            label_visibility="collapsed",
        )
        importar_arquivo(uploaded_file)
        if "importacao" in st.session_state:
            situacao, texto = st.session_state["importacao"]
            if situacao == "ok":
                st.success(texto, icon="✨")
            else:
                st.error(texto, icon="📄")

    user_story = st.text_area("User Story", key="user_story", height=120)
    criterios = st.text_area("Critérios de Aceite", key="criterios", height=180)
    criterios_numerados = numerar_criterios(criterios)
    st.caption(
        f"História: {len(user_story.strip())}/{MAX_CARACTERES} · "
        f"Critérios: {len(criterios_numerados)}/{MAX_CARACTERES} caracteres · "
        f"{total_criterios(criterios)} critério(s)"
    )
    if criterios_numerados:
        renumerado = criterios_numerados != "\n".join(l.strip() for l in criterios.splitlines() if l.strip())
        with st.expander("🔢 Critérios numerados (como serão enviados)", expanded=renumerado):
            # "1\." evita que o Markdown renumere a lista e esconda a numeração real
            st.markdown("  \n".join(re.sub(r"^(\d+)\.", r"\1\\.", l) for l in criterios_numerados.splitlines()))
    gerar_btn = st.button("🚀 Gerar Modelo e Testes", key="gerar", type="primary", width="stretch")

if gerar_btn:
    st.session_state.pop("execucao", None)
    st.session_state.pop("resultado", None)
    sistema_alvo = st.session_state["sistema_alvo"] or None
    nome_exemplo = st.session_state["exemplo"]
    erros_entrada = validar_entrada(user_story, criterios_numerados)
    recusa = motivo_recusa_demo(nome_exemplo, user_story, criterios) if modo_demo and not erros_entrada else None
    with col_output:
        if erros_entrada:
            st.error("\n\n".join(erros_entrada), icon="✋")
        elif recusa:
            st.warning(recusa, icon="🎬")
        else:
            try:
                t0 = time.perf_counter()
                with st.status(f"Processando com {modelo_selecionado}…", expanded=True) as status:
                    if modo_demo:
                        for msg in (
                            "Carregando o modelo de referência do exemplo…",
                            "Gerando cenários e scripts…",
                        ):
                            st.write(f"⏳ {msg}")
                            time.sleep(0.3)
                        modelo_gerado = modelo_de_referencia(nome_exemplo)
                        tentativas, duracao_backend, historico = None, None, []
                    else:
                        st.write("⏳ Consultando o backend e o LLM…")
                        resposta = chamar_backend(
                            user_story,
                            criterios_numerados,
                            modelo_selecionado,
                            api_key=api_key_custom or None,
                            sistema=sistema_alvo,
                        )
                        modelo_gerado = resposta["modelo"]
                        tentativas, duracao_backend = resposta.get("tentativas"), resposta.get("duracao")
                        historico = resposta.get("historico") or []
                    status.update(label="Análise concluída ✅", state="complete", expanded=False)
                duracao = time.perf_counter() - t0
                st.session_state["resultado"] = {
                    "modelo": modelo_gerado,
                    "artefatos": gerar_artefatos(modelo_gerado, sistema_alvo),
                    "sistema": sistema_alvo,
                    "demo": modo_demo,
                    "total_criterios": total_criterios(criterios_numerados),
                    "tempo_execucao": f"{duracao:.2f}s",
                    "motor_usado": modelo_selecionado,
                    "tentativas": tentativas,
                    "duracao_backend": duracao_backend,
                    "historico": historico,
                }
            except RuntimeError as e:
                st.error(str(e), icon="🚨")

with col_output:
    st.markdown('<div class="card-title">📦 Artefatos Gerados <span class="badge">MBT &amp; BDD</span></div>',
                unsafe_allow_html=True)
    res = st.session_state.get("resultado")

    if not res:
        st.markdown(
            '<div class="empty"><div class="icon">🧠</div><h3>Nenhuma análise ainda</h3>'
            "Preencha os requisitos à esquerda e clique em <b>Gerar Modelo e Testes</b>.</div>",
            unsafe_allow_html=True,
        )
    else:
        modelo = res["modelo"]
        cobertos = criterios_cobertos(modelo)
        total = res["total_criterios"]
        completo = total > 0 and len(cobertos) >= total
        tempo_ex = res.get("tempo_execucao", "—")
        motor_ex = res.get("motor_usado", modelo_selecionado)

        st.markdown(
            f"""
            <div class="metrics">
              <div class="metric"><div class="v">{len(modelo['estados'])}</div><div class="l">Estados</div></div>
              <div class="metric"><div class="v">{len(modelo['transicoes'])}</div><div class="l">Transições</div></div>
              <div class="metric {'ok' if completo else 'warn'}"><div class="v">{len(cobertos)}/{total}</div>
                  <div class="l">Critérios</div></div>
              <div class="metric info"><div class="v" style="font-size:1.1rem;padding-top:8px">{estado_inicial(modelo)}</div>
                  <div class="l">Inicial</div></div>
              <div class="metric"><div class="v" style="font-size:1.35rem;padding-top:4px">{tempo_ex}</div>
                  <div class="l">Latência ({'Demo' if res['demo'] else 'Real'})</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if res.get("tentativas"):
            st.caption(
                f"Backend: {res['tentativas']} tentativa(s) em {res['duracao_backend']:.1f}s com {motor_ex}."
            )

        artefatos = res["artefatos"]
        if res["sistema"]:
            if st.button("▶️ Executar testes nas duas variantes", key="executar", type="primary"):
                with st.spinner("Executando os testes…"):
                    st.session_state["execucao"] = executar_testes(artefatos)
            if "execucao" in st.session_state:
                render_execucao(st.session_state["execucao"])
        else:
            st.info(
                "Sem sistema alvo, os artefatos são esqueletos: os testes falham até um sistema ser conectado.",
                icon="🧱",
            )

        abas = st.tabs(["📊 Grafo", "🧠 Análise", "🔀 Transições", "📝 BDD (Gherkin)", "💻 Pytest", "🧩 JSON"])
        if res["demo"]:
            for aba in abas:
                with aba:
                    st.info(AVISO_DEMO, icon="🎬")
        tab1, tab_analise, tab2, tab3, tab4, tab5 = abas
        with tab1:
            codigo_mermaid = modelo_para_mermaid(modelo)
            render_mermaid(codigo_mermaid)
            with st.expander("📋 Código Mermaid (stateDiagram-v2)"):
                st.code(codigo_mermaid, language="text")
        with tab_analise:
            render_analise(modelo, res.get("historico") or [])
        with tab2:
            linhas = [
                {"Id": t["id"], "De": t["de"], "Evento": t["evento"], "Guarda": t.get("guarda") or "—",
                 "Ações": "; ".join(t.get("acoes") or []) or "—", "Para": t["para"],
                 "Critérios": ", ".join(f"#{n}" for n in t.get("criterios") or []) or "—"}
                for t in modelo["transicoes"]
            ]
            st.dataframe(linhas, width="stretch", hide_index=True)
        with tab3:
            st.code(artefatos.feature, language="gherkin")
            st.download_button(f"⬇️ Baixar {artefatos.nome_feature}", data=artefatos.feature,
                               file_name=artefatos.nome_feature, mime="text/plain")
        with tab4:
            st.code(artefatos.script, language="python")
            st.download_button(f"⬇️ Baixar {artefatos.nome_script}", data=artefatos.script,
                               file_name=artefatos.nome_script, mime="text/x-python")
        with tab5:
            st.json(modelo)
