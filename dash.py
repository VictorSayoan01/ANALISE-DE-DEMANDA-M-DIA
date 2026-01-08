import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Análise de Demanda – Energisa PB",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Fundo principal */
    .stApp {
        background-color: white;
    }

    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #0B3C5D;
    }

    /* Texto geral */
    p, span, label, div {
        color: #0B3C5D;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Métricas */
    div[data-testid="stMetricValue"] {
        color: #0B3C5D;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.image("TAUREN_LOGO.png", width=150)

st.title("📊 Análise de Demanda e Opção Tarifária – Grupo A (Energisa-PB)")
st.caption("Dashboard técnico para análise de demanda, energia, fator de potência e opção tarifária")

# =========================================================
# FUNÇÃO DE LEITURA E TRATAMENTO
# =========================================================
@st.cache_data
def carregar_dados(arquivo_pot, arquivo_fp):

    # ---------- POTÊNCIA ATIVA ----------
    df_pot = pd.read_csv(arquivo_pot, sep=",", decimal=".")
    df_pot = df_pot.drop(columns=["Nome"], errors="ignore")

    df_pot["Data"] = pd.to_datetime(
        df_pot["Data"],
        format="%d/%m/%Y, %H:%M:%S",
        errors="coerce"
    )

    df_pot = df_pot.dropna(subset=["Data"])
    df_pot["P_kW"] = df_pot["Potência Ativa"] / 1000
    df_pot = df_pot.drop(columns=["Potência Ativa"])

    df_pot = df_pot.set_index("Data").sort_index()
    df_pot = df_pot[~df_pot.index.duplicated(keep="first")]

    # ---------- FATOR DE POTÊNCIA ----------
    df_fp = pd.read_csv(arquivo_fp, sep=",", decimal=".")
    df_fp = df_fp.drop(columns=["Nome"], errors="ignore")

    df_fp["Data"] = pd.to_datetime(
        df_fp["Data"],
        format="%d/%m/%Y, %H:%M:%S",
        errors="coerce"
    )

    df_fp = df_fp.dropna(subset=["Data"])
    df_fp = df_fp.set_index("Data").sort_index()
    df_fp = df_fp[~df_fp.index.duplicated(keep="first")]

    # ---------- JOIN TEMPORAL ----------
    df = df_pot.join(df_fp, how="inner")

    return df

# =========================================================
# CARREGAR DADOS
# =========================================================
arquivo_pot = r"D:\OneDrive\SAYOAN\PROJETOS - TAUREN ENERGIA\PROJETOS DE INSTALAÇÃO DE BAIXA TENSÃO\PROJETO 10 - NAVEGANTES\ANALISE DE DEMANDA MÉDIA\historico--17-12-2025.csv"
arquivo_fp  = r"D:\OneDrive\SAYOAN\PROJETOS - TAUREN ENERGIA\PROJETOS DE INSTALAÇÃO DE BAIXA TENSÃO\PROJETO 10 - NAVEGANTES\ANALISE DE DEMANDA MÉDIA\historico--17-12-2025fp.csv"

df = carregar_dados(arquivo_pot, arquivo_fp)

# =========================================================
# FILTRO DE PERÍODO
# =========================================================
st.sidebar.header("📆 Filtro de Período")

data_inicio = st.sidebar.date_input(
    "Data inicial",
    df.index.min().date()
)

data_fim = st.sidebar.date_input(
    "Data final",
    df.index.max().date()
)

df = df.loc[
    (df.index.date >= data_inicio) &
    (df.index.date <= data_fim)
]

# =========================================================
# CLASSIFICAÇÃO PONTA / FORA DE PONTA – ENERGISA PB
# =========================================================
df["hora"] = df.index.hour
df["dia_semana"] = df.index.weekday

df["Periodo"] = "Fora de Ponta"

cond_ponta = (
    (df["hora"] >= 18) &
    (df["hora"] < 21) &
    (df["dia_semana"] < 5)
)

df.loc[cond_ponta, "Periodo"] = "Ponta"

# =========================================================
# INDICADORES
# =========================================================
demanda_max = df["P_kW"].max()
demanda_media = df["P_kW"].mean()
energia_total = df["P_kW"].sum()
fp_medio = df["Fator de Potência"].mean()
demanda_recomendada = demanda_max * 1.10
# =========================================================
# KPIs
# =========================================================
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("⚡ Demanda Máx (kW)", f"{demanda_max:.2f}")
col2.metric("📈 Demanda Média (kW)", f"{demanda_media:.2f}")
col3.metric("🔋 Energia Total (kWh)", f"{energia_total:,.0f}")
col4.metric("🔌 FP Médio", f"{fp_medio:.3f}")
col5.metric("📊 Demanda Recomendada (kW)", f"{demanda_recomendada:.2f}")

# ALERTA FP
if fp_medio < 0.92:
    st.error("⚠️ Fator de potência médio abaixo do limite regulatório (0,92).")
else:
    st.success("✔ Fator de potência dentro do limite regulatório.")

# =========================================================
# GRÁFICO – PERFIL DE POTÊNCIA
# =========================================================
st.subheader("📈 Perfil de Potência Ativa")

fig1, ax1 = plt.subplots(figsize=(12,4))
ax1.plot(df.index, df["P_kW"])
ax1.set_xlabel("Tempo")
ax1.set_ylabel("kW")
ax1.grid(True)

st.pyplot(fig1)

# =========================================================
# DEMANDA MÉDIA DIÁRIA
# =========================================================
st.subheader("📊 Demanda Média Diária")

demanda_diaria = df["P_kW"].resample("D").mean()

fig2, ax2 = plt.subplots(figsize=(10,4))
ax2.plot(demanda_diaria.index, demanda_diaria.values)
ax2.set_xlabel("Data")
ax2.set_ylabel("kW")
ax2.grid(True)

st.pyplot(fig2)

# =========================================================
# SIMULAÇÃO TARIFÁRIA – ENERGISA PB (A4)
# =========================================================
st.subheader("💰 Simulação Tarifária")

energia_ponta = df[df["Periodo"] == "Ponta"]["P_kW"].sum()
energia_fora  = df[df["Periodo"] == "Fora de Ponta"]["P_kW"].sum()

demanda_ponta = df[df["Periodo"] == "Ponta"]["P_kW"].max()
demanda_fora  = df[df["Periodo"] == "Fora de Ponta"]["P_kW"].max()

# Tarifa Verde
fatura_verde = (
    demanda_max * 24.72 +
    energia_ponta * 1.60297 +
    energia_fora  * 0.28655
)

# Tarifa Azul
fatura_azul = (
    demanda_ponta * 48.77 +
    demanda_fora  * 24.72 +
    energia_ponta * 0.42014 +
    energia_fora  * 0.28655
)

colv, cola, colb = st.columns(3)

colv.metric("💚 Tarifa Verde (R$)", f"{fatura_verde:,.2f}")
cola.metric("💙 Tarifa Azul (R$)", f"{fatura_azul:,.2f}")

if fatura_verde < fatura_azul:
    st.success(f"Modalidade recomendada: **HORÁRIA VERDE** – Economia estimada de R$ {(fatura_azul - fatura_verde):,.2f}")
else:
    st.success(f"Modalidade recomendada: **HORÁRIA AZUL** – Economia estimada de R$ {(fatura_verde - fatura_azul):,.2f}")

# =========================================================
# TABELA E EXPORTAÇÃO
# =========================================================
st.subheader("📋 Base de Dados Consolidada")

st.dataframe(df, use_container_width=True)

st.download_button(
    label="📥 Baixar base consolidada (CSV)",
    data=df.to_csv(sep=";", decimal=",", encoding="utf-8-sig"),
    file_name="base_consolidada.csv",
    mime="text/csv"
)
