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

col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.image("TAUREN_LOGO.png", width=120)

with col_title:
    st.title("📊 Análise de Demanda e Opção Tarifária – Grupo A")
    st.caption("Energisa-PB • Engenharia Elétrica • Análise Técnica")

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
arquivo_pot = st.sidebar.file_uploader(
    "Upload – Potência Ativa (CSV)",
    type=["csv"]
)

arquivo_fp = st.sidebar.file_uploader(
    "Upload – Fator de Potência (CSV)",
    type=["csv"]
)

bandeira_selecionada = st.selectbox(
    "Bandeira Tarifária de Dezembro/2025",
    ["Verde", "Amarela", "Vermelha Nível 1", "Vermelha Nível 2"]
)

if bandeira_selecionada == "Verde":
    bandeira_valor = 0.0
elif bandeira_selecionada == "Amarela":
    bandeira_valor = 0.01885
elif bandeira_selecionada == "Vermelha Nível 1":
    bandeira_valor = 0.04400
else:  # Vermelha Nível 2
    bandeira_valor = 0.09100

if arquivo_pot is None or arquivo_fp is None:
    st.info("⬅️ Faça upload dos dois arquivos para iniciar a análise.")
    st.stop()

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
st.divider()
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
st.divider()
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
st.divider()
st.subheader("📊 Demanda Média Diária")

demanda_diaria = df["P_kW"].resample("D").mean()

fig2, ax2 = plt.subplots(figsize=(10,4))
ax2.plot(demanda_diaria.index, demanda_diaria.values)
ax2.set_xlabel("Data")
ax2.set_ylabel("kW")
ax2.grid(True)

st.pyplot(fig2)

# =========================================================
# FATOR DE POTÊNCIA
# =========================================================
st.divider()
st.subheader("📈 Fator de Potência")

fator_potencia = df["Fator de Potência"]

fig3, ax3 = plt.subplots(figsize=(10,4))
ax3.plot(fator_potencia.index, fator_potencia.values)
ax3.set_xlabel("Data")
ax3.set_ylabel("Fator de Potência")
ax3.grid(True)

st.pyplot(fig3)
# =========================================================
# SIMULAÇÃO TARIFÁRIA – ENERGISA PB (A4)
# =========================================================
st.divider()
st.subheader("💰 Simulação Tarifária")

energia_ponta = df[df["Periodo"] == "Ponta"]["P_kW"].sum()
energia_fora  = df[df["Periodo"] == "Fora de Ponta"]["P_kW"].sum()

demanda_ponta = df[df["Periodo"] == "Ponta"]["P_kW"].max()
demanda_fora  = df[df["Periodo"] == "Fora de Ponta"]["P_kW"].max()

# Valor do ICMS na Paraíba e Tarifa:
icms_pb = 0.20  
tarifa_B = 0.85

#Tarifa Grupo B:
custo_base = energia_total * tarifa_B
custo_bandeira = energia_total * bandeira_valor
subtotal_sem_icms = custo_base + custo_bandeira
fatura_B_icms = subtotal_sem_icms * (1 + icms_pb)

# Valores de Tarifas:
# Verde:
tar_demanda_verde = 24.72
tar_e_ponta_verde = 1.60297
tar_e_fora_verde = 0.28655

# Azul:
demanda_ponta_azul = 48.77
demanda_fora_azul = 24.72 
energia_ponta_azul = 0.42014 
energia_fora_azul = 0.28655

# Tarifa Verde
fatura_verde = (
    demanda_max *  tar_demanda_verde +
    energia_ponta *  tar_e_ponta_verde +
    energia_fora  * tar_e_fora_verde
)

# Tarifa Azul
fatura_azul = (
    demanda_ponta * 48.77 +
    demanda_fora  * 24.72 +
    energia_ponta * 0.42014 +
    energia_fora  * 0.28655
)

# custo energia ponta/fora de ponta com bandeira
energia_total_verde_com_bandeira = (
    energia_ponta * (tar_e_ponta_verde + bandeira_valor) +
    energia_fora * (tar_e_fora_verde + bandeira_valor)
)

energia_total_azul_com_bandeira = (
    energia_ponta * (energia_ponta_azul + bandeira_valor) +
    energia_fora * (energia_fora_azul + bandeira_valor)
)

# Parte de demanda não sofre bandeira, mas sofre ICMS direta
custo_demanda_verde = demanda_max * tar_demanda_verde
custo_demanda_azul = (
    demanda_ponta * demanda_ponta_azul +
    demanda_fora * demanda_fora_azul
)

# subtotal sem ICMS:
subtotal_verde = custo_demanda_verde + energia_total_verde_com_bandeira
subtotal_azul  = custo_demanda_azul + energia_total_azul_com_bandeira

# aplicando ICMS:
fatura_verde_icms = subtotal_verde * (1 + icms_pb)
fatura_azul_icms  = subtotal_azul * (1 + icms_pb)


dif_verde = fatura_verde - fatura_B_icms
dif_azul  = fatura_azul  - fatura_B_icms

colv, cola, colb, cole = st.columns(4)

colv.metric(
    "💚 Tarifa Verde – Grupo A (R$)",
    f"{fatura_verde:,.2f}"
)

cola.metric(
    "💙 Tarifa Azul – Grupo A (R$)",
    f"{fatura_azul:,.2f}"
)

colb.metric(
    "⚡ Tarifa Convencional – Grupo B (R$)",
    f"{fatura_B_icms:,.2f}"
)

cole.metric(
    "💰 Diferença Verde × Grupo B (R$)",
    f"{(fatura_verde - fatura_B_icms):,.2f}"
)


if dif_verde < 0 and dif_verde < dif_azul:
    st.success(
        f"📉 A migração para o **Grupo A – Horária Verde** "
        f"pode gerar economia estimada de R$ {abs(dif_verde):,.2f} "
        f"em relação ao Grupo B."
    )
elif dif_azul < 0:
    st.success(
        f"📉 A migração para o **Grupo A – Horária Azul** "
        f"pode gerar economia estimada de R$ {abs(dif_azul):,.2f} "
        f"em relação ao Grupo B."
    )
else:
    st.warning(
        "📌 Com base no perfil atual de carga, a migração para o Grupo A "
        "não apresenta vantagem econômica imediata."
    )

if fatura_verde < fatura_azul:
    st.success(f"📉 A tarifa Verde é recomendada, gerando uma economia de R$ {(fatura_azul - fatura_verde):,.2f}")
else:
    st.success(f"📉 A tarifa Verde é recomendada, gerando uma economia de R$ {(fatura_verde - fatura_azul):,.2f}")

# =========================================================
# TABELA E EXPORTAÇÃO
# =========================================================
st.divider()
st.subheader("📋 Base de Dados Consolidada")

st.dataframe(df, use_container_width=True)

st.download_button(
    label="📥 Baixar base consolidada (CSV)",
    data=df.to_csv(sep=";", decimal=",", encoding="utf-8-sig"),
    file_name="base_consolidada.csv",
    mime="text/csv"
)

st.divider()
st.subheader("📝 Conclusão Técnica")

st.write(f"""
Com base nos dados analisados no período selecionado, a instalação apresentou
demanda máxima de **{demanda_max:.2f} kW**, com demanda média de **{demanda_media:.2f} kW**.

A demanda contratável recomendada é de **{demanda_recomendada:.2f} kW**.
O fator de potência médio foi de **{fp_medio:.3f}**, estando {"abaixo" if fp_medio < 0.92 else "dentro"} do limite regulatório.

A modalidade tarifária mais vantajosa é **{'Horária Verde' if fatura_verde < fatura_azul else 'Horária Azul'}**.
""")
