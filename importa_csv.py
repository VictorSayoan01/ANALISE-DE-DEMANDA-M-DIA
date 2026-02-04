import pandas as pd
import sqlite3

# ==============================
# CONFIGURAÇÕES
# ==============================
DB_NAME = "dados.db"
CSV_POTENCIA = "Potencia_Ativa.csv"
CSV_FP = "fator_de_potencia.csv"

# ==============================
# CONEXÃO COM BANCO
# ==============================
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# ==============================
# CRIAR TABELAS
# ==============================
cursor.execute("""
CREATE TABLE IF NOT EXISTS potencia_ativa (
    data TEXT PRIMARY KEY,
    potencia_kw REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fator_potencia (
    data TEXT PRIMARY KEY,
    fp REAL
)
""")

conn.commit()

# ==============================
# IMPORTAR POTÊNCIA ATIVA
# ==============================
df_pot = pd.read_csv(CSV_POTENCIA, sep=",", decimal=".")
df_pot["Data"] = pd.to_datetime(
    df_pot["Data"],
    format="%d/%m/%Y, %H:%M:%S",
    errors="coerce"
)

df_pot = df_pot.drop_duplicates(subset=["Data"])
df_pot = df_pot.dropna(subset=["Data"])
df_pot["potencia_kw"] = df_pot["Potência Ativa"] / 1000
df_pot = df_pot[["Data", "potencia_kw"]]

df_pot.to_sql(
    "potencia_ativa",
    conn,
    if_exists="replace",
    index=False
)

# ==============================
# IMPORTAR FATOR DE POTÊNCIA
# ==============================
df_fp = pd.read_csv(CSV_FP, sep=",", decimal=".")
df_fp["Data"] = pd.to_datetime(
    df_fp["Data"],
    format="%d/%m/%Y, %H:%M:%S",
    errors="coerce"
)

df_fp = df_fp.drop_duplicates(subset=["Data"])
df_fp = df_fp.dropna(subset=["Data"])
df_fp = df_fp.rename(columns={"Fator de Potência": "fp"})
df_fp = df_fp[["Data", "fp"]]

df_fp.to_sql(
    "fator_potencia",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(" CSVs importados com sucesso para o banco SQLite!")
