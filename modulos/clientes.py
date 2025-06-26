
import streamlit as st

def mostrar_clientes(df):
    st.markdown("## 👤 Clientes")

    nombre_usuario = st.session_state.get("nombre_colaborador", "")
    es_admin = nombre_usuario == "Ivan Manrique" or st.session_state.get("rol", "").lower() == "admin"

    lista_clientes = sorted(df["CLIENTE"].dropna().unique().tolist())
    cliente_seleccionado = st.selectbox("🔍 Selecciona un cliente", options=[""] + lista_clientes)

    if cliente_seleccionado:
        st.markdown(f"### 🧾 {cliente_seleccionado}")

        df_cliente = df[df["CLIENTE"] == cliente_seleccionado]

        cups_unicos = df_cliente["CUPS"].dropna().unique().tolist()
        cups_seleccionado = st.selectbox("⚡ Selecciona un CUPS", options=[""] + cups_unicos)

        if cups_seleccionado:
            df_cups = df_cliente[df_cliente["CUPS"] == cups_seleccionado]

            st.markdown("#### 📍 Detalle del CUPS seleccionado")
            direccion = df_cups["DIRECCION DE SUMINISTRO"].dropna().unique()
            tarifa = df_cups["TARIFA"].dropna().unique()
            comercializadora = df_cups["COMERCIALIZADORA"].dropna().unique()
            consumo = df_cups["CONSUMO"].sum() if "CONSUMO" in df_cups.columns else 0
            veces_facturado = len(df_cups)

            comision_total = df_cups["Comision"].sum() if es_admin else df_cups["Comision COLABORADOR"].sum()

            st.markdown(f"- 📬 **Dirección de suministro:** {direccion[0] if len(direccion) > 0 else 'No disponible'}")
            st.markdown(f"- 🏷️ **Tarifa:** {', '.join(tarifa) if tarifa.any() else 'No disponible'}")
            st.markdown(f"- 🏢 **Comercializadora:** {', '.join(comercializadora) if comercializadora.any() else 'No disponible'}")
            st.markdown(f"- 🔁 **Veces facturado (registros):** {veces_facturado}")
            st.markdown(f"- ⚡ **Consumo total:** {consumo:,.2f} kWh")
            st.markdown(f"- 💰 **Comisión total acumulada:** {comision_total:,.2f} €")

            for campo, etiqueta in [("contrato", "Contrato"), ("Estudio", "Estudio"), ("Factura", "Factura")]:
                if campo in df_cups.columns:
                    enlaces = df_cups[campo].dropna().unique()
                    if len(enlaces) > 0:
                        st.markdown(f"- 📎 **{etiqueta}:** [Ver archivo]({enlaces[0]})")

            st.markdown("#### 📅 Registros asociados")

            columnas_ocultas = []
            if not es_admin:
                columnas_ocultas = ["Comision", "Factura IVAN"]

            columnas_finales = [col for col in df_cups.columns if col not in columnas_ocultas]
            st.dataframe(df_cups[columnas_finales], use_container_width=True)
