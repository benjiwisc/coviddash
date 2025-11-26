import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard COVID 2020–2022", layout="wide")

logo_url = "https://upload.wikimedia.org/wikipedia/commons/7/7a/UCSC%2C_Universidad_Cat%C3%B3lica_de_la_Sant%C3%ADsima_Concepci%C3%B3n.png"
st.image(logo_url, width=150)
st.write("Autores: Matias Gonzalez Plaza, Juliano Muñoz Sepulveda, Benjamin Cifuentes Rubilar.")

st.title("🦠 Dashboard COVID-19 (2020–2022)")
st.write("Análisis con filtros por continente, país, fechas, rebrote, tasas y gráficos diarios.")

@st.cache_data
def cargar_datos():
    return pd.read_csv("data/data_final.zip",parse_dates=["fecha_archivo"],low_memory=False)


df = cargar_datos()

columnas_requeridas = [
    "fecha_archivo", "continente", "pais",
    "confirmados", "activos", "recuperados", "fallecidos"
]
faltantes = [c for c in columnas_requeridas if c not in df.columns]
if faltantes:
    st.error(f"Dataset incompleto. Faltan: {faltantes}")
    st.stop()

st.sidebar.header("Filtros")

continentes = sorted(df["continente"].dropna().unique())
continente_sel = st.sidebar.selectbox("Continente", continentes)

df_cont = df[df["continente"] == continente_sel]

paises = sorted(df_cont["pais"].dropna().unique())
pais_sel = st.sidebar.selectbox("🇺🇳 País", paises)

df_pais = df_cont[df_cont["pais"] == pais_sel]

min_fecha = df_pais["fecha_archivo"].min()
max_fecha = df_pais["fecha_archivo"].max()

rango = st.sidebar.date_input(
    "Rango de fechas",
    value=[min_fecha, max_fecha],
    min_value=min_fecha,
    max_value=max_fecha,
)

if len(rango) == 2:
    inicio_f, fin_f = rango
    df_pais = df_pais[
        (df_pais["fecha_archivo"] >= pd.to_datetime(inicio_f)) &
        (df_pais["fecha_archivo"] <= pd.to_datetime(fin_f))
    ]

st.markdown("Indicadores del período seleccionado")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Casos Confirmados", f"{df_pais['confirmados'].sum():,}")
col2.metric("Activos", f"{df_pais['activos'].sum():,}")
col3.metric("Recuperados", f"{df_pais['recuperados'].sum():,}")
col4.metric("Fallecidos", f"{df_pais['fallecidos'].sum():,}")

df_time = df_pais.groupby("fecha_archivo")[["confirmados", "fallecidos", "recuperados"]].sum().reset_index()


st.markdown("---")
st.subheader(f"Evolución acumulada de casos confirmados en {pais_sel}")

fig = px.line(
    df_time,
    x="fecha_archivo",
    y="confirmados",
    labels={
        "fecha_archivo": "Fecha",
        "confirmados": "Casos Confirmados"
    },
    markers=True,
    template="plotly_dark",
    title=f"Confirmados acumulados en {pais_sel}"
)
st.plotly_chart(fig, use_container_width=True)

df_time["confirmados_diarios"] = df_time["confirmados"].diff().clip(lower=0)

st.subheader("Casos Confirmados diarios")

fig = px.bar(
    df_time,
    x="fecha_archivo",
    y="confirmados_diarios",
    labels={
        "fecha_archivo": "Fecha",
        "confirmados_diarios": "Casos Confirmados Diario"
    },
    template="plotly_dark",
    title="Confirmados nuevos por día",
)
st.plotly_chart(fig, use_container_width=True)

df_time["muertes_diarias"] = df_time["fallecidos"].diff().clip(lower=0)

st.subheader("Cantidad de muertes diarias")

fig = px.line(
    df_time,
    x="fecha_archivo",
    y="muertes_diarias",
    labels={
        "fecha_archivo": "Fecha",
        "muertes_diarias": "Casos de mueretes Diario"
    },
    markers=True,
    template="plotly_dark",
    title="Muertes nuevas por día"
)
st.plotly_chart(fig, use_container_width=True)

df_time["recuperados_diarios"] = df_time["recuperados"].diff().clip(lower=0)

st.subheader("Cantidad de recuperados diarios")

fig = px.area(
    df_time,
    x="fecha_archivo",
    y="recuperados_diarios",
    labels={
        "fecha_archivo": "Fecha",
        "recuperados_diarios": "Recuperados a Diario"
    },
    template="plotly_dark",
    title="Recuperados nuevos por día",
    color="recuperados_diarios"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Detección de rebrote")

df_time["nuevos"] = df_time["confirmados_diarios"]
df_time["rebrote"] = (df_time["nuevos"].rolling(3).mean() == 0) & (df_time["nuevos"].shift(-1) > 0)

if df_time["rebrote"].any():
    st.warning("**Rebrote detectado**: se registró un día con 0 nuevos casos seguido de un aumento.")
else:
    st.success("No hay rebrote en el período.")

st.subheader("Tasa de crecimiento del período")

inicio_val = df_time["confirmados"].iloc[0]
fin_val = df_time["confirmados"].iloc[-1]

if inicio_val > 0:
    crecimiento_bruto = fin_val - inicio_val
    factor = fin_val / inicio_val
else:
    crecimiento_bruto = 0
    factor = 1
if factor <= 2:
    tasa_texto = f"{(factor-1)*100:.2f}%"
else:
    tasa_texto = f"{factor:.2f} veces (crecimiento multiplicativo)"

st.metric("Tasa de crecimiento", tasa_texto)

st.markdown("---")
st.subheader("Datos filtrados")
st.dataframe(df_pais, use_container_width=True)
st.markdown("---")
st.subheader("📌 Conclusiones")

conf_tot = df_pais['confirmados'].sum()
muertes_tot = df_pais['fallecidos'].sum()
recup_tot = df_pais['recuperados'].sum()
activos_tot = df_pais['activos'].sum()
dias = len(df_time)

prom_diario = df_time["confirmados_diarios"].mean()
pico = df_time["confirmados_diarios"].max()
fecha_pico = df_time.loc[df_time["confirmados_diarios"].idxmax(), "fecha_archivo"].date()

conclusiones = []

if crecimiento_bruto > 0:
    conclusiones.append(
        f"El país mostró un **crecimiento total de {crecimiento_bruto:,} casos**, "
        f"equivalente a una variación de **{tasa_texto}** durante el período analizado."
    )

if prom_diario > 0:
    conclusiones.append(
        f"El promedio diario de contagios fue de **{prom_diario:.0f} casos**, "
        f"mientras que el **mas alto ocurrió el {fecha_pico}** con **{pico:,} nuevos contagios**."
    )

if recup_tot > muertes_tot:
    conclusiones.append(
        f"Las recuperaciones (**{recup_tot:,}**) superan ampliamente a los fallecimientos "
        f"(**{muertes_tot:,}**), lo que sugiere una evolución sanitaria favorable."
    )
else:
    conclusiones.append(
        f"Los fallecimientos (**{muertes_tot:,}**) son altos en relación a los recuperados "
        f"(**{recup_tot:,}**), indicando un período crítico."
    )

if df_time["rebrote"].any():
    conclusiones.append(
        "Se detectó **posible rebrote**, ya que se observaron días con 0 contagios "
        "seguido de un aumento significativo."
    )
else:
    conclusiones.append(
        "No se identificaron señales de rebrote en el período seleccionado."
    )

if activos_tot > (conf_tot * 0.20):
    conclusiones.append(
        f"El número de casos activos (**{activos_tot:,}**) representa un porcentaje "
        f"elevado del total acumulado, indicando presencia del virus."
    )

for c in conclusiones:
    st.write(f"- {c}")
