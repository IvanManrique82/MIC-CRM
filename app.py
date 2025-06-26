import streamlit as st

# ─── 1) DEBE SER LO PRIMERO ────────────────────────────────────────────────
st.set_page_config(page_title="CRM MIC CONSULTORES", layout="wide")

# ─── 2) IMPORTS GENERALES ──────────────────────────────────────────────────
import pandas as pd
from modulos.dashboard import mostrar_dashboard
from modulos.clientes import mostrar_clientes
from modulos.admin_contratos import mostrar_carga_contratos   # ← sección admin
from modulos.notion_api import obtener_datos_notion
from modulos.sidebar import (
    mostrar_login_pantalla_completa,
    mostrar_sidebar,
)

# ─── 3) TOKENS DESDE SECRETS ───────────────────────────────────────────────
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID  = st.secrets["DATABASE_ID"]

# ─── 4) ESTILOS, USUARIOS, LOGIN ───────────────────────────────────────────
with open("assets/styles.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

usuarios_df = pd.read_excel("usuarios.xlsx")

if not st.session_state.get("logueado", False):
    mostrar_login_pantalla_completa(usuarios_df)
    st.stop()

mostrar_sidebar(usuarios_df)

# Extra: botón solo para admin
if st.session_state.rol.lower() == "admin":
    with st.sidebar:
        st.markdown("---")
        if st.button("📝 Carga contratos"):
            st.session_state.seccion = "Carga contratos"

# ─── 5) FUNCIÓN PRINCIPAL ──────────────────────────────────────────────────
def main() -> None:
    df = obtener_datos_notion(NOTION_TOKEN, DATABASE_ID)
    if df.empty:
        st.warning("No se pudieron cargar los datos desde Notion.")
        return

    # filtro colaborador
    if st.session_state.rol.lower() != "admin":
        df = df[df["USUARIO"] == st.session_state.nombre_colaborador]

    # Router
    seccion = st.session_state.seccion
    if seccion == "Dashboard":
        mostrar_dashboard(df)
    elif seccion == "Clientes":
        mostrar_clientes(df)
    elif seccion == "Facturas":
        st.subheader("📄 Facturas por Comunidad")
        try:
            with open("facturas.html", "r", encoding="utf-8") as f:
                st.components.v1.html(f.read(), height=800, scrolling=True)
        except FileNotFoundError:
            st.warning("No se encontró facturas.html.")
    elif seccion == "Carga contratos" and st.session_state.rol.lower() == "admin":
        mostrar_carga_contratos(df, DATABASE_ID)   # ← le pasamos el ID
    else:
        st.error("Sección no reconocida o sin permisos.")

# ─── 6) EJECUTA ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
