from pathlib import Path
import pandas as pd
import streamlit as st

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS DE HIERARQUIA TIPOGRÁFICA
# =============================================================================
st.set_page_config(
    page_title="Relatório Comparativo de Votação",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    h2 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #F3F4F6 !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.2rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #D1D5DB !important;
        margin-top: 1rem !important;
        margin-bottom: 0.3rem !important;
    }
    h4, h5 {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #E5E7EB !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.2rem !important;
    }
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        padding: 2px 0px !important;
        margin-bottom: -6px !important;
    }
    .stButton button {
        padding: 2px 8px !important;
        height: auto !important;
        font-size: 13px !important;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CARREGAMENTO E FUNÇÕES DE CONSOLIDAÇÃO DE DADOS
# =============================================================================
PASTA_DATA = Path("data")

@st.cache_data(show_spinner="Carregando bases estaduais de 2026...")
def carregar_bases():
    arqs_1t = [PASTA_DATA / "votos_t1_2026_presidente.csv", Path("votos_t1_2026_presidente.csv")]
    arqs_2t = [PASTA_DATA / "votos_t2_2026_presidente.csv", Path("votos_t2_2026_presidente.csv")]
    
    p_1t = next((p for p in arqs_1t if p.exists()), None)
    p_2t = next((p for p in arqs_2t if p.exists()), None)
    
    if not p_1t or not p_2t:
        st.error("❌ Arquivos de dados não encontrados na pasta 'data/' ou na raiz.")
        st.stop()

    df_1t = pd.read_csv(p_1t, sep=";", encoding="latin1", low_memory=False)
    df_2t = pd.read_csv(p_2t, sep=";", encoding="latin1", low_memory=False)

    df_1t.columns = [str(c).strip().lower() for c in df_1t.columns]
    df_2t.columns = [str(c).strip().lower() for c in df_2t.columns]

    return df_1t, df_2t

def calc_pct(parte, total):
    return (parte / total * 100) if total and total > 0 else 0.0

def consolidar_indicadores(df_sub):
    if df_sub.empty:
        return {
            "aptos": 0, "secoes": 0, "locais": 0,
            "lula": 0, "flavio": 0, "outros": 0, "brancos": 0, "nulos": 0, "abstencao": 0,
            "validos": 0, "comparecimento": 0
        }

    secoes = df_sub["nr_secao"].nunique() if "nr_secao" in df_sub.columns else 0
    locais = df_sub["nm_local_votacao"].nunique() if "nm_local_votacao" in df_sub.columns else 0

    cols_secao = [c for c in ["nr_zona", "nr_secao"] if c in df_sub.columns]
    if cols_secao and "qt_aptos" in df_sub.columns:
        secoes_df = df_sub.groupby(cols_secao).first().reset_index()
        aptos = int(pd.to_numeric(secoes_df["qt_aptos"], errors="coerce").fillna(0).sum())
        abstencao = int(pd.to_numeric(secoes_df["qt_abstencoes"], errors="coerce").fillna(0).sum())
        comp = int(pd.to_numeric(secoes_df["qt_comparecimento"], errors="coerce").fillna(0).sum())
    else:
        aptos, abstencao, comp = 0, 0, 0

    pivot = df_sub.groupby("nr_votavel")["qt_votos"].sum().to_dict()

    lula = int(pivot.get(13, 0))
    flavio = int(pivot.get(22, 0))
    brancos = int(pivot.get(95, 0))
    nulos = int(pivot.get(96, 0))

    outros = int(sum(v for nr, v in pivot.items() if nr not in [13, 22, 95, 96]))

    validos = lula + flavio + outros
    if comp == 0:
        comp = validos + brancos + nulos

    return {
        "aptos": aptos, "secoes": secoes, "locais": locais,
        "lula": lula, "flavio": flavio, "outros": outros,
        "brancos": brancos, "nulos": nulos, "abstencao": abstencao,
        "validos": validos, "comparecimento": comp
    }

def gerar_tabela_relatorio(t1, t2, aptos_ref):
    linhas = [
        ("Lula", t1["lula"], t2["lula"], True),
        ("Flávio Bolsonaro", t1["flavio"], t2["flavio"], True),
        ("Outros Candidatos", t1["outros"], t2["outros"], True),
        ("Voto em Branco", t1["brancos"], t2["brancos"], False),
        ("Voto Nulo", t1["nulos"], t2["nulos"], False),
        ("Abstenção", t1["abstencao"], t2["abstencao"], False),
    ]

    dados_tabela = []
    for rotulo, v1, v2, eh_valido in linhas:
        val1_base = t1["validos"] if eh_valido else None
        val2_base = t2["validos"] if eh_valido else None

        pct_val_1t = calc_pct(v1, val1_base) if val1_base else None
        pct_val_2t = calc_pct(v2, val2_base) if val2_base else None

        pct_aptos_1t = calc_pct(v1, aptos_ref)
        pct_aptos_2t = calc_pct(v2, aptos_ref)

        eh_outros_2t = (rotulo == "Outros Candidatos" and v2 == 0)
        
        v2_str = "-" if eh_outros_2t else f"{v2:,.0f}".replace(",", ".")
        pct_val_2t_str = "-" if (eh_outros_2t or pct_val_2t is None) else f"{pct_val_2t:.2f}%".replace(".", ",")
        pct_aptos_2t_str = "-" if eh_outros_2t else f"{pct_aptos_2t:.2f}%".replace(".", ",")

        dados_tabela.append({
            "Categoria": rotulo,
            "1º Turno": f"{v1:,.0f}".replace(",", "."),
            "2º Turno": v2_str,
            "Percentual dos Válidos (1º Turno)": f"{pct_val_1t:.2f}%".replace(".", ",") if pct_val_1t is not None else "-",
            "Percentual dos Válidos (2º Turno)": pct_val_2t_str,
            "Percentual dos Eleitores Aptos (1º Turno)": f"{pct_aptos_1t:.2f}%".replace(".", ","),
            "Percentual dos Eleitores Aptos (2º Turno)": pct_aptos_2t_str,
        })

    return pd.DataFrame(dados_tabela)

# =============================================================================
# 3. APLICAÇÃO PRINCIPAL (STREAMLIT)
# =============================================================================
def main():
    base_mg_1t, base_mg_2t = carregar_bases()

    muns_1t = base_mg_1t[["cd_municipio", "nm_municipio"]].drop_duplicates()
    muns_2t = base_mg_2t[["cd_municipio", "nm_municipio"]].drop_duplicates()
    muns_todos = pd.concat([muns_1t, muns_2t]).drop_duplicates().sort_values("nm_municipio")

    opcoes_mun = {
        f"{row['nm_municipio']} (Cód. {row['cd_municipio']})": row["cd_municipio"]
        for _, row in muns_todos.iterrows()
    }
    lista_nomes = list(opcoes_mun.keys())

    # --- TELA INICIAL DE SELEÇÃO DE MUNICÍPIO ---
    if "municipio_selecionado" not in st.session_state:
        st.session_state["municipio_selecionado"] = None

    if st.session_state["municipio_selecionado"] is None:
        st.title("📊 Relatório Comparativo de Votação")
        st.caption("Eleições Presidenciais 2026 — Dados Oficiais consolidados de Minas Gerais")
        st.markdown("---")
        
        st.markdown("### 🏙️ Bem-vindo! Escolha o município para iniciar a análise:")
        
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            mun_escolhido = st.selectbox("Selecione o Município:", lista_nomes, label_visibility="collapsed")
        with col_btn:
            st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Carregar Relatório", use_container_width=True):
                st.session_state["municipio_selecionado"] = mun_escolhido
                st.rerun()
        
        st.stop()  # Interrompe a execução até que o usuário escolha a cidade

    # --- BOTÃO NA SIDEBAR PARA TROCAR DE CIDADE A QUALQUER MOMENTO ---
    st.sidebar.header("⚙️ Configurações")
    if st.sidebar.button("🔄 Trocar de Município"):
        st.session_state["municipio_selecionado"] = None
        st.rerun()

    mun_label_sel = st.session_state["municipio_selecionado"]
    cod_municipio = opcoes_mun[mun_label_sel]

    base_municip_1t = base_mg_1t[base_mg_1t["cd_municipio"] == cod_municipio]
    base_municip_2t = base_mg_2t[base_mg_2t["cd_municipio"] == cod_municipio]

    nome_cidade = base_municip_1t["nm_municipio"].iloc[0] if not base_municip_1t.empty else base_municip_2t["nm_municipio"].iloc[0]

    t1_mun = consolidar_indicadores(base_municip_1t)
    t2_mun = consolidar_indicadores(base_municip_2t)

    aptos_mun = t2_mun["aptos"] if t2_mun["aptos"] > 0 else t1_mun["aptos"]
    secoes_mun = t2_mun["secoes"] if t2_mun["secoes"] > 0 else t1_mun["secoes"]
    locais_mun = t2_mun["locais"] if t2_mun["locais"] > 0 else t1_mun["locais"]

    # --- CABEÇALHO PRINCIPAL DA APLICAÇÃO ---
    st.title("📊 Relatório Comparativo de Votação")
    st.caption(f"Eleições Presidenciais 2026 — Município: **{nome_cidade}**")

    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("📍 Município", nome_cidade, f"Código: {cod_municipio}")
    with k2: st.metric("👥 Eleitores Aptos", f"{aptos_mun:,.0f}".replace(",", "."))
    with k3: st.metric("🗳️ Quantidade de Seções", f"{secoes_mun:,.0f}".replace(",", "."))
    with k4: st.metric("🏫 Locais de Votação", f"{locais_mun:,.0f}".replace(",", "."))

    st.markdown("---")

    # =========================================================================
    # SEÇÃO 1: TABELA E INDICADORES DE DOMÍNIO MUNICIPAL
    # =========================================================================
    st.header("1. Votação no Município")

    df_relatorio_mun = gerar_tabela_relatorio(t1_mun, t2_mun, aptos_mun)
    st.dataframe(
        df_relatorio_mun,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Categoria": st.column_config.TextColumn("Candidato / Voto", width="medium"),
            "1º Turno": st.column_config.TextColumn("1º Turno"),
            "2º Turno": st.column_config.TextColumn("2º Turno"),
            "Percentual dos Válidos (1º Turno)": st.column_config.TextColumn("% Válidos (1º T)"),
            "Percentual dos Válidos (2º Turno)": st.column_config.TextColumn("% Válidos (2º T)"),
            "Percentual dos Eleitores Aptos (1º Turno)": st.column_config.TextColumn("% Aptos (1º T)"),
            "Percentual dos Eleitores Aptos (2º Turno)": st.column_config.TextColumn("% Aptos (2º T)"),
        }
    )

    st.markdown("#### 📈 Variação dos Candidatos e Categorias no 2º Turno (Município)")
    st.caption("Crescimento ou redução de votos absolutos e variação percentual (2º Turno vs 1º Turno)")

    v_1t_m = {"Lula": t1_mun["lula"], "Flávio Bolsonaro": t1_mun["flavio"], "Voto em Branco": t1_mun["brancos"], "Voto Nulo": t1_mun["nulos"], "Abstenção": t1_mun["abstencao"]}
    v_2t_m = {"Lula": t2_mun["lula"], "Flávio Bolsonaro": t2_mun["flavio"], "Voto em Branco": t2_mun["brancos"], "Voto Nulo": t2_mun["nulos"], "Abstenção": t2_mun["abstencao"]}

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Lula", f"{v_2t_m['Lula']:,}".replace(",", "."), f"{v_2t_m['Lula'] - v_1t_m['Lula']:+,}".replace(",", "."))
    with c2: st.metric("Flávio Bolsonaro", f"{v_2t_m['Flávio Bolsonaro']:,}".replace(",", "."), f"{v_2t_m['Flávio Bolsonaro'] - v_1t_m['Flávio Bolsonaro']:+,}".replace(",", "."))
    with c3: st.metric("Votos em Branco", f"{v_2t_m['Voto em Branco']:,}".replace(",", "."), f"{v_2t_m['Voto em Branco'] - v_1t_m['Voto em Branco']:+,}".replace(",", "."))
    with c4: st.metric("Votos Nulos", f"{v_2t_m['Voto Nulo']:,}".replace(",", "."), f"{v_2t_m['Voto Nulo'] - v_1t_m['Voto Nulo']:+,}".replace(",", "."))
    with c5: st.metric("Abstenção", f"{v_2t_m['Abstenção']:,}".replace(",", "."), f"{v_2t_m['Abstenção'] - v_1t_m['Abstenção']:+,}".replace(",", "."))

    linhas_var_m = [
        ("Lula", t1_mun["lula"], t2_mun["lula"], True),
        ("Flávio Bolsonaro", t1_mun["flavio"], t2_mun["flavio"], True),
        ("Voto em Branco", t1_mun["brancos"], t2_mun["brancos"], False),
        ("Voto Nulo", t1_mun["nulos"], t2_mun["nulos"], False),
        ("Abstenção", t1_mun["abstencao"], t2_mun["abstencao"], False),
    ]

    dados_var_m = []
    for rotulo, v1, v2, eh_valido in linhas_var_m:
        diff_abs = v2 - v1
        pct_abs_cresc = calc_pct(diff_abs, v1) if v1 > 0 else 0.0

        if eh_valido:
            diff_pp_validos = f"{calc_pct(v2, t2_mun['validos']) - calc_pct(v1, t1_mun['validos']):+.2f} p.p.".replace(".", ",")
        else:
            diff_pp_validos = "-"

        diff_pp_aptos = f"{calc_pct(v2, aptos_mun) - calc_pct(v1, aptos_mun):+.2f} p.p.".replace(".", ",")

        dados_var_m.append({
            "Categoria": rotulo,
            "Variação Absoluta (Votos)": f"{diff_abs:+,}".replace(",", "."),
            "Crescimento Relativo (%)": f"{pct_abs_cresc:+.2f}%".replace(".", ","),
            "Var. nos Válidos (p.p.)": diff_pp_validos,
            "Var. nos Aptos (p.p.)": diff_pp_aptos,
        })

    st.dataframe(
        pd.DataFrame(dados_var_m),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Categoria": st.column_config.TextColumn("Candidato / Voto", width="medium"),
            "Variação Absoluta (Votos)": st.column_config.TextColumn("Diferença de Votos (2T - 1T)"),
            "Crescimento Relativo (%)": st.column_config.TextColumn("Crescimento % vs 1T"),
            "Var. nos Válidos (p.p.)": st.column_config.TextColumn("Variação % Válidos (p.p.)"),
            "Var. nos Aptos (p.p.)": st.column_config.TextColumn("Variação % Aptos (p.p.)"),
        }
    )

    # --- PLACAR DE DOMÍNIO TERRITORIAL ---
    s1_df = base_municip_1t.groupby(["nr_zona", "nr_secao", "nr_votavel"])["qt_votos"].sum().unstack(fill_value=0)
    s2_df = base_municip_2t.groupby(["nr_zona", "nr_secao", "nr_votavel"])["qt_votos"].sum().unstack(fill_value=0)

    for c in [13, 22]:
        if c not in s1_df.columns: s1_df[c] = 0
        if c not in s2_df.columns: s2_df[c] = 0

    loc1_df = base_municip_1t.groupby(["nm_local_votacao", "nr_votavel"])["qt_votos"].sum().unstack(fill_value=0)
    loc2_df = base_municip_2t.groupby(["nm_local_votacao", "nr_votavel"])["qt_votos"].sum().unstack(fill_value=0)

    for c in [13, 22]:
        if c not in loc1_df.columns: loc1_df[c] = 0
        if c not in loc2_df.columns: loc2_df[c] = 0

    sec_venc_1t_lula = sum(s1_df[13] > s1_df[22]) if not s1_df.empty else 0
    sec_venc_1t_flavio = sum(s1_df[22] > s1_df[13]) if not s1_df.empty else 0
    sec_venc_2t_lula = sum(s2_df[13] > s2_df[22]) if not s2_df.empty else 0
    sec_venc_2t_flavio = sum(s2_df[22] > s2_df[13]) if not s2_df.empty else 0

    tot_secoes_calc = len(s2_df) if len(s2_df) > 0 else (len(s1_df) if len(s1_df) > 0 else 1)

    loc_venc_1t_lula = sum(loc1_df[13] > loc1_df[22]) if not loc1_df.empty else 0
    loc_venc_1t_flavio = sum(loc1_df[22] > loc1_df[13]) if not loc1_df.empty else 0
    loc_venc_2t_lula = sum(loc2_df[13] > loc2_df[22]) if not loc2_df.empty else 0
    loc_venc_2t_flavio = sum(loc2_df[22] > loc2_df[13]) if not loc2_df.empty else 0

    tot_locais_calc = len(loc2_df) if len(loc2_df) > 0 else (len(loc1_df) if len(loc1_df) > 0 else 1)

    st.markdown("#### 🏆 Placar de Domínio Territorial (Locais e Seções Vencidos)")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        with st.container(border=True):
            st.markdown("##### 🔴 **Lula**")
            st.markdown(f"* **Locais Vencidos:** 1ºT: **{loc_venc_1t_lula}** ({loc_venc_1t_lula/tot_locais_calc*100:.1f}%) | 2ºT: **{loc_venc_2t_lula}** ({loc_venc_2t_lula/tot_locais_calc*100:.1f}%)".replace(".", ","))
            st.markdown(f"* **Seções Vencidas:** 1ºT: **{sec_venc_1t_lula}** ({sec_venc_1t_lula/tot_secoes_calc*100:.1f}%) | 2ºT: **{sec_venc_2t_lula}** ({sec_venc_2t_lula/tot_secoes_calc*100:.1f}%)".replace(".", ","))

    with col_p2:
        with st.container(border=True):
            st.markdown("##### 🟢 **Flávio Bolsonaro**")
            st.markdown(f"* **Locais Vencidos:** 1ºT: **{loc_venc_1t_flavio}** ({loc_venc_1t_flavio/tot_locais_calc*100:.1f}%) | 2ºT: **{loc_venc_2t_flavio}** ({loc_venc_2t_flavio/tot_locais_calc*100:.1f}%)".replace(".", ","))
            st.markdown(f"* **Seções Vencidas:** 1ºT: **{sec_venc_1t_flavio}** ({sec_venc_1t_flavio/tot_secoes_calc*100:.1f}%) | 2ºT: **{sec_venc_2t_flavio}** ({sec_venc_2t_flavio/tot_secoes_calc*100:.1f}%)".replace(".", ","))

    st.markdown("---")

    # =========================================================================
    # SEÇÃO 2: ANÁLISE DA VIRADA E DINÂMICA DE VOTOS
    # =========================================================================
    st.header("2. Análise da Virada e Dinâmica de Votos")
    st.caption("Indicadores de movimentação, viradas de liderança e crescimento comparativo entre os candidatos")

    secoes_unificadas = s1_df.index.union(s2_df.index)
    
    sec_analytics = []
    for sec_key in secoes_unificadas:
        l1 = int(s1_df.loc[sec_key, 13]) if sec_key in s1_df.index else 0
        f1 = int(s1_df.loc[sec_key, 22]) if sec_key in s1_df.index else 0
        l2 = int(s2_df.loc[sec_key, 13]) if sec_key in s2_df.index else 0
        f2 = int(s2_df.loc[sec_key, 22]) if sec_key in s2_df.index else 0

        v1 = "Lula" if l1 > f1 else ("Flávio" if f1 > l1 else "Empate/Outros")
        v2 = "Lula" if l2 > f2 else ("Flávio" if f2 > l2 else "Empate")

        sec_analytics.append({"secao": sec_key, "diff_lula": l2 - l1, "diff_flavio": f2 - f1, "venc_1": v1, "venc_2": v2})

    df_sec_an = pd.DataFrame(sec_analytics)
    tot_sec = len(df_sec_an) if len(df_sec_an) > 0 else 1

    loc_analytics = []
    for loc_nome in loc1_df.index.union(loc2_df.index):
        l1 = int(loc1_df.loc[loc_nome, 13]) if loc_nome in loc1_df.index else 0
        f1 = int(loc1_df.loc[loc_nome, 22]) if loc_nome in loc1_df.index else 0
        l2 = int(loc2_df.loc[loc_nome, 13]) if loc_nome in loc2_df.index else 0
        f2 = int(loc2_df.loc[loc_nome, 22]) if loc_nome in loc2_df.index else 0

        v1 = "Lula" if l1 > f1 else ("Flávio" if f1 > l1 else "Empate/Outros")
        v2 = "Lula" if l2 > f2 else ("Flávio" if f2 > l1 else "Empate")

        loc_analytics.append({"local": loc_nome, "diff_lula": l2 - l1, "diff_flavio": f2 - f1, "venc_1": v1, "venc_2": v2})

    df_loc_an = pd.DataFrame(loc_analytics)
    tot_loc = len(df_loc_an) if len(df_loc_an) > 0 else 1

    st.markdown("#### 🟢🔴 Aumento vs Queda de Votos no 2º Turno")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        with st.container(border=True):
            st.markdown("##### 🔴 **Desempenho — Lula**")
            st.markdown(f"* **Ganhou Votos:** em **{len(df_loc_an[df_loc_an['diff_lula'] > 0])}** locais ({len(df_loc_an[df_loc_an['diff_lula'] > 0])/tot_loc*100:.1f}%) e **{len(df_sec_an[df_sec_an['diff_lula'] > 0])}** seções ({len(df_sec_an[df_sec_an['diff_lula'] > 0])/tot_sec*100:.1f}%)".replace(".", ","))
            st.markdown(f"* **Perdeu Votos:** em **{len(df_loc_an[df_loc_an['diff_lula'] < 0])}** locais ({len(df_loc_an[df_loc_an['diff_lula'] < 0])/tot_loc*100:.1f}%) e **{len(df_sec_an[df_sec_an['diff_lula'] < 0])}** seções ({len(df_sec_an[df_sec_an['diff_lula'] < 0])/tot_sec*100:.1f}%)".replace(".", ","))

    with col_g2:
        with st.container(border=True):
            st.markdown("##### 🟢 **Desempenho — Flávio Bolsonaro**")
            st.markdown(f"* **Ganhou Votos:** em **{len(df_loc_an[df_loc_an['diff_flavio'] > 0])}** locais ({len(df_loc_an[df_loc_an['diff_flavio'] > 0])/tot_loc*100:.1f}%) e **{len(df_sec_an[df_sec_an['diff_flavio'] > 0])}** seções ({len(df_sec_an[df_sec_an['diff_flavio'] > 0])/tot_sec*100:.1f}%)".replace(".", ","))
            st.markdown(f"* **Perdeu Votos:** em **{len(df_loc_an[df_loc_an['diff_flavio'] < 0])}** locais ({len(df_loc_an[df_loc_an['diff_flavio'] < 0])/tot_loc*100:.1f}%) e **{len(df_sec_an[df_sec_an['diff_flavio'] < 0])}** seções ({len(df_sec_an[df_sec_an['diff_flavio'] < 0])/tot_sec*100:.1f}%)".replace(".", ","))

    st.markdown("#### ⚡ Crescimento Relativo (Quem expandiu mais votos?)")
    
    sec_lula_maior = len(df_sec_an[df_sec_an['diff_lula'] > df_sec_an['diff_flavio']])
    sec_flavio_maior = len(df_sec_an[df_sec_an['diff_flavio'] > df_sec_an['diff_lula']])
    sec_empate_cresc = len(df_sec_an[df_sec_an['diff_lula'] == df_sec_an['diff_flavio']])

    pct_sec_lula = (sec_lula_maior / tot_sec * 100) if tot_sec > 0 else 0.0
    pct_sec_flavio = (sec_flavio_maior / tot_sec * 100) if tot_sec > 0 else 0.0
    pct_sec_empate = (sec_empate_cresc / tot_sec * 100) if tot_sec > 0 else 0.0

    c_r1, c_r2, c_r3 = st.columns(3)
    with c_r1: 
        st.metric("🔴 Lula cresceu MAIS", f"{len(df_loc_an[df_loc_an['diff_lula'] > df_loc_an['diff_flavio']])} locais", f"{sec_lula_maior} seções ({pct_sec_lula:.1f}%)".replace(".", ","))
    with c_r2: 
        st.metric("🟢 Flávio cresceu MAIS", f"{len(df_loc_an[df_loc_an['diff_flavio'] > df_loc_an['diff_lula']])} locais", f"{sec_flavio_maior} seções ({pct_sec_flavio:.1f}%)".replace(".", ","))
    with c_r3: 
        st.metric("⚖️ Crescimento Igual", f"{len(df_loc_an[df_loc_an['diff_lula'] == df_loc_an['diff_flavio']])} locais", f"{sec_empate_cresc} seções ({pct_sec_empate:.1f}%)".replace(".", ","))

    st.markdown("#### 🔄 Viradas de Liderança (Locais que mudaram de lado)")
    viradas_f_para_l = df_loc_an[(df_loc_an["venc_1"] == "Flávio") & (df_loc_an["venc_2"] == "Lula")]
    viradas_l_para_f = df_loc_an[(df_loc_an["venc_1"] == "Lula") & (df_loc_an["venc_2"] == "Flávio")]

    v_col1, v_col2 = st.columns(2)
    with v_col1:
        with st.container(border=True):
            st.markdown("##### 🔄 **Viradas para Lula (🔴)**")
            st.markdown(f"**{len(viradas_f_para_l)}** locais mudaram de **Flávio (1ºT) ➡️ Lula (2ºT)**")
            if not viradas_f_para_l.empty:
                for _, r in viradas_f_para_l.iterrows():
                    st.markdown(f"* 🏫 **{r['local']}** (+{r['diff_lula']} votos)")
            else:
                st.caption("Nenhum local teve virada direta a favor de Lula.")

    with v_col2:
        with st.container(border=True):
            st.markdown("##### 🔄 **Viradas para Flávio (🟢)**")
            st.markdown(f"**{len(viradas_l_para_f)}** locais mudaram de **Lula (1ºT) ➡️ Flávio (2ºT)**")
            if not viradas_l_para_f.empty:
                for _, r in viradas_l_para_f.iterrows():
                    st.markdown(f"* 🏫 **{r['local']}** (+{r['diff_flavio']} votos)")
            else:
                st.caption("Nenhum local teve virada direta a favor de Flávio.")

    st.markdown("---")

    # =========================================================================
    # SEÇÃO 3: VOTAÇÃO POR LOCAL DE VOTAÇÃO
    # =========================================================================
    st.header("3. Votação por Local de Votação")
    st.caption("Explore o desempenho eleitoral em cada ponto de votação e seção da cidade")

    locais_1t = set(base_municip_1t["nm_local_votacao"].dropna().unique()) if "nm_local_votacao" in base_municip_1t.columns else set()
    locais_2t = set(base_municip_2t["nm_local_votacao"].dropna().unique()) if "nm_local_votacao" in base_municip_2t.columns else set()
    lista_locais = sorted(list(locais_1t.union(locais_2t)))

    if not lista_locais:
        st.info("Nenhum local de votação encontrado para este município.")
        st.stop()

    busca_local = st.text_input("🔍 Pesquisar local de votação:", "", placeholder="Digite o nome do local ou escola...")
    locais_filtrados = [l for l in lista_locais if busca_local.lower() in l.lower()] if busca_local else lista_locais

    if "local_aberto" not in st.session_state:
        st.session_state["local_aberto"] = None

    def truncar_nome(nome, limite=40):
        return nome[:limite] + "..." if len(nome) > limite else nome

    modo_vis = st.radio("Modo de Visualização:", ["🖥️ Tabela Completa (Desktop)", "📱 Modo Compacto (Mobile/Busca)"], horizontal=True, label_visibility="collapsed")

    if modo_vis == "🖥️ Tabela Completa (Desktop)":
        col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([4.2, 2, 2, 2, 0.6])
        with col_h1: st.caption("**LOCAL DE VOTAÇÃO**")
        with col_h2: st.caption("**1º TURNO**")
        with col_h3: st.caption("**2º TURNO**")
        with col_h4: st.caption("**ELEITORES (SEC.)**")
        with col_h5: st.caption("**AÇÃO**")

        st.markdown("<hr style='margin: 4px 0px 10px 0px;'>", unsafe_allow_html=True)

        for idx_loc, loc in enumerate(locais_filtrados):
            d1_loc = base_municip_1t[base_municip_1t["nm_local_votacao"] == loc]
            d2_loc = base_municip_2t[base_municip_2t["nm_local_votacao"] == loc]

            t1_l = consolidar_indicadores(d1_loc)
            t2_l = consolidar_indicadores(d2_loc)

            aptos_l = t2_l["aptos"] if t2_l["aptos"] > 0 else t1_l["aptos"]
            secoes_l = t2_l["secoes"] if t2_l["secoes"] > 0 else t1_l["secoes"]
            aptos_fmt = f"{aptos_l:,.0f}".replace(",", ".")

            if t2_l["validos"] > 0:
                if t2_l["flavio"] > t2_l["lula"]:
                    venc_2t = f"🟢 Flávio ({calc_pct(t2_l['flavio'], t2_l['validos']):.1f}%)".replace(".", ",")
                elif t2_l["lula"] > t2_l["flavio"]:
                    venc_2t = f"🔴 Lula ({calc_pct(t2_l['lula'], t2_l['validos']):.1f}%)".replace(".", ",")
                else:
                    venc_2t = "⚪ Empate"
            else:
                venc_2t = "⚪ -"

            if t1_l["validos"] > 0:
                if t1_l["flavio"] > t1_l["lula"] and t1_l["flavio"] > t1_l["outros"]:
                    venc_1t = f"🟢 Flávio ({calc_pct(t1_l['flavio'], t1_l['validos']):.1f}%)".replace(".", ",")
                elif t1_l["lula"] > t1_l["flavio"] and t1_l["lula"] > t1_l["outros"]:
                    venc_1t = f"🔴 Lula ({calc_pct(t1_l['lula'], t1_l['validos']):.1f}%)".replace(".", ",")
                else:
                    venc_1t = f"🟡 Outros ({calc_pct(t1_l['outros'], t1_l['validos']):.1f}%)".replace(".", ",")
            else:
                venc_1t = "⚪ -"

            c1, c2, c3, c4, c5 = st.columns([4.2, 2, 2, 2, 0.6])

            with c1: st.markdown(f"🏫 **{truncar_nome(loc)}**", help=loc)
            with c2: st.markdown(venc_1t)
            with c3: st.markdown(venc_2t)
            with c4: st.markdown(f"👥 **{aptos_fmt}** ({secoes_l} sec.)")
            with c5:
                is_open = (st.session_state["local_aberto"] == loc)
                btn_label = "❌" if is_open else "🔍"
                if st.button(btn_label, key=f"btn_exp_{idx_loc}", help="Ver detalhamento completo"):
                    st.session_state["local_aberto"] = None if is_open else loc
                    st.rerun()

            st.markdown("<hr style='margin: 2px 0px; border: 0.2px solid #262730;'>", unsafe_allow_html=True)

            if st.session_state["local_aberto"] == loc:
                with st.container(border=True):
                    secoes_1t = set(d1_loc["nr_secao"].dropna().unique()) if "nr_secao" in d1_loc.columns else set()
                    secoes_2t = set(d2_loc["nr_secao"].dropna().unique()) if "nr_secao" in d2_loc.columns else set()
                    lista_secoes_loc = sorted([int(s) for s in secoes_1t.union(secoes_2t)])

                    col_titulo, col_seletor_sec = st.columns([3, 1])
                    with col_titulo: st.markdown(f"##### 📊 Detalhamento Completo — {loc}")
                    with col_seletor_sec:
                        opcoes_secao = ["Todas as Seções"] + [f"Seção {s}" for s in lista_secoes_loc]
                        secao_sel = st.selectbox("Filtrar Seção:", opcoes_secao, key=f"sel_sec_{idx_loc}")

                    if secao_sel != "Todas as Seções":
                        nr_sec_num = int(secao_sel.replace("Seção ", ""))
                        d1_view = d1_loc[d1_loc["nr_secao"] == nr_sec_num]
                        d2_view = d2_loc[d2_loc["nr_secao"] == nr_sec_num]
                        txt_escopo = f"Seção {nr_sec_num}"
                    else:
                        d1_view, d2_view = d1_loc, d2_loc
                        txt_escopo = "Todas as Seções"

                    t1_v, t2_v = consolidar_indicadores(d1_view), consolidar_indicadores(d2_view)
                    aptos_v = t2_v["aptos"] if t2_v["aptos"] > 0 else t1_v["aptos"]
                    secoes_v = t2_v["secoes"] if t2_v["secoes"] > 0 else t1_v["secoes"]

                    st.caption(f"Escopo: **{txt_escopo}** | Eleitores Aptos: **{aptos_v:,.0f}**.replace(',', '.') | Quantidade de Seções: **{secoes_v}** | Participação na Cidade: **{calc_pct(aptos_v, aptos_mun):.2f}%**".replace(".", ","))

                    df_relatorio_loc = gerar_tabela_relatorio(t1_v, t2_v, aptos_v)
                    st.dataframe(df_relatorio_loc, hide_index=True, use_container_width=True)

                    st.markdown(f"**Variação no 2º Turno ({txt_escopo}):**")
                    v_1t_l = {"Lula": t1_v["lula"], "Flávio Bolsonaro": t1_v["flavio"], "Voto em Branco": t1_v["brancos"], "Voto Nulo": t1_v["nulos"], "Abstenção": t1_v["abstencao"]}
                    v_2t_l = {"Lula": t2_v["lula"], "Flávio Bolsonaro": t2_v["flavio"], "Voto em Branco": t2_v["brancos"], "Voto Nulo": t2_v["nulos"], "Abstenção": t2_v["abstencao"]}

                    cm1, cm2, cm3, cm4, cm5 = st.columns(5)
                    with cm1: st.metric("Lula", f"{v_2t_l['Lula']:,}".replace(",", "."), f"{v_2t_l['Lula'] - v_1t_l['Lula']:+,}".replace(",", "."))
                    with cm2: st.metric("Flávio Bolsonaro", f"{v_2t_l['Flávio Bolsonaro']:,}".replace(",", "."), f"{v_2t_l['Flávio Bolsonaro'] - v_1t_l['Flávio Bolsonaro']:+,}".replace(",", "."))
                    with cm3: st.metric("Votos em Branco", f"{v_2t_l['Voto em Branco']:,}".replace(",", "."), f"{v_2t_l['Voto em Branco'] - v_1t_l['Voto em Branco']:+,}".replace(",", "."))
                    with cm4: st.metric("Votos Nulos", f"{v_2t_l['Voto Nulo']:,}".replace(",", "."), f"{v_2t_l['Voto Nulo'] - v_1t_l['Voto Nulo']:+,}".replace(",", "."))
                    with cm5: st.metric("Abstenção", f"{v_2t_l['Abstenção']:,}".replace(",", "."), f"{v_2t_l['Abstenção'] - v_1t_l['Abstenção']:+,}".replace(",", "."))

    else:
        local_sel_mob = st.selectbox("Selecione ou digite o local de votação:", lista_locais)
        
        if local_sel_mob:
            d1_loc = base_municip_1t[base_municip_1t["nm_local_votacao"] == local_sel_mob]
            d2_loc = base_municip_2t[base_municip_2t["nm_local_votacao"] == local_sel_mob]

            t1_l, t2_l = consolidar_indicadores(d1_loc), consolidar_indicadores(d2_loc)
            aptos_l = t2_l["aptos"] if t2_l["aptos"] > 0 else t1_l["aptos"]

            secoes_1t = set(d1_loc["nr_secao"].dropna().unique()) if "nr_secao" in d1_loc.columns else set()
            secoes_2t = set(d2_loc["nr_secao"].dropna().unique()) if "nr_secao" in d2_loc.columns else set()
            lista_secoes_loc = sorted([int(s) for s in secoes_1t.union(secoes_2t)])

            secao_sel_m = st.selectbox("Filtrar Seção:", ["Todas as Seções"] + [f"Seção {s}" for s in lista_secoes_loc], key="mob_sec_sel")

            if secao_sel_m != "Todas as Seções":
                nr_sec = int(secao_sel_m.replace("Seção ", ""))
                d1_v, d2_v = d1_loc[d1_loc["nr_secao"] == nr_sec], d2_loc[d2_loc["nr_secao"] == nr_sec]
            else:
                d1_v, d2_v = d1_loc, d2_loc

            t1_v, t2_v = consolidar_indicadores(d1_v), consolidar_indicadores(d2_v)
            aptos_v = t2_v["aptos"] if t2_v["aptos"] > 0 else t1_v["aptos"]

            st.markdown(f"##### 🏫 {local_sel_mob}")
            st.caption(f"Eleitores Aptos: **{aptos_v:,.0f}**.replace(',', '.') | Seções: **{t2_v['secoes']}**")

            df_relatorio_loc = gerar_tabela_relatorio(t1_v, t2_v, aptos_v)
            st.dataframe(df_relatorio_loc, hide_index=True, use_container_width=True)

            v_1t_l = {"Lula": t1_v["lula"], "Flávio Bolsonaro": t1_v["flavio"], "Voto em Branco": t1_v["brancos"], "Voto Nulo": t1_v["nulos"], "Abstenção": t1_v["abstencao"]}
            v_2t_l = {"Lula": t2_v["lula"], "Flávio Bolsonaro": t2_v["flavio"], "Voto em Branco": t2_v["brancos"], "Voto Nulo": t2_v["nulos"], "Abstenção": t2_v["abstencao"]}

            m_col1, m_col2 = st.columns(2)
            with m_col1: st.metric("Lula", f"{v_2t_l['Lula']:,}".replace(",", "."), f"{v_2t_l['Lula'] - v_1t_l['Lula']:+,}".replace(",", "."))
            with m_col2: st.metric("Flávio", f"{v_2t_l['Flávio Bolsonaro']:,}".replace(",", "."), f"{v_2t_l['Flávio Bolsonaro'] - v_1t_l['Flávio Bolsonaro']:+,}".replace(",", "."))

if __name__ == "__main__":
    main()