# 📊 Dashboard Comparativo Eleitoral (1º e 2º Turno - Presidencial 2026)

Aplicação web interativa desenvolvida em Python e Streamlit para análise detalhada do desempenho eleitoral comparativo entre o 1º e o 2º turno das Eleições Presidenciais nos municípios de Minas Gerais.

## 🚀 Funcionalidades
- **Seleção Dinâmica de Município:** Consulta completa para qualquer cidade de MG.
- **Seção 1: Panorama Municipal:** Tabela consolidada com percentuais sobre válidos e aptos, variação absoluta e placar de domínio territorial (locais/seções vencidos).
- **Seção 2: Análise da Virada:** Métricas detalhadas de ganho/perda de votos, ritmo de crescimento relativo e locais que viraram de liderança.
- **Seção 3: Detalhamento por Local e Seção:** Consulta micro com suporte a busca rápida e alternância entre visão desktop fluida e mobile compacto.

## 🛠️ Tecnologias Utilizadas
- **Python 3.11+**
- **Streamlit** (Interface gráfica interativa)
- **Pandas** (Tratamento e manipulação de dados)

## 🗂️ Estrutura de Dados
Os dados de votação por seção e local foram extraídos das bases oficiais do TSE e consolidados na pasta `data/`.