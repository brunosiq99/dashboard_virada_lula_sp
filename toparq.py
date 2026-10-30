import streamlit as st
import pandas as pd
@st.cache_data(show_spinner="Carregando bases estaduais de 2026...")
def carregar_bases():
    # Aponta para os novos ficheiros .parquet otimizados
    p_1t = PASTA_DATA / "votos_t1_2026_presidente.parquet"
    p_2t = PASTA_DATA / "votos_t2_2026_presidente.parquet"
    
    if not p_1t.exists() or not p_2t.exists():
        st.error("❌ Ficheiros .parquet não encontrados na pasta 'data/'.")
        st.stop()

    # Leitura ultrarrápida e otimizada via Parquet
    df_1t = pd.read_parquet(p_1t)
    df_2t = pd.read_parquet(p_2t)

    df_1t.columns = [str(c).strip().lower() for c in df_1t.columns]
    df_2t.columns = [str(c).strip().lower() for c in df_2t.columns]

    return df_1t, df_2t