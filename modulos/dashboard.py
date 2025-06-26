# ── dashboard.py ─────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from datetime import datetime
from .asistente_gpt import responder_consulta     # <- tu helper GPT

# ───────────────── FUNCIÓN TARJETA (KPIs) ──────────────────
def tarjeta(container, css_class: str, icon_fa: str, titulo: str, valor) -> None:
    container.markdown(
        f"""
        <div class="kpi-card {css_class}">
          <i class="fa-solid {icon_fa} kpi-icon"></i>
          <div class="kpi-title">{titulo}</div>
          <div class="kpi-value">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ───────────────────── DASHBOARD PRINCIPAL ─────────────────
def mostrar_dashboard(df: pd.DataFrame) -> None:
    """Pantalla principal del CRM."""

    # 1) Fechas a datetime
    df["FECHA ACTIVACION"] = pd.to_datetime(df["FECHA ACTIVACION"], errors="coerce")

    # 2) Modo claro/oscuro
    dark = st.toggle("🌙 Modo oscuro", key="dark_mode")
    st.markdown(
        f"<script>document.body.classList.toggle('dark-mode',{str(dark).lower()});</script>",
        unsafe_allow_html=True,
    )

    # 3) CSS global extra (KPIs + tablas bonitas)
    st.markdown(
        """
        <style>
          /* efecto zoom icono KPI */
          .kpi-card{overflow:hidden}
          .kpi-card:hover .kpi-icon{transform:scale(1.15)}
          .kpi-icon{transition:transform .3s ease}

          /* tabla sin índice + cebra + bordes redondeados */
          .tabla-pendientes{border-collapse:collapse;width:100%;
                            border:1px solid #e0e0e0;border-radius:8px;overflow:hidden}
          .tabla-pendientes th{background:#f0f2f6;font-weight:bold;padding:6px 10px;
                               position:sticky;top:0;z-index:1}
          .tabla-pendientes td{padding:6px 10px}
          .tabla-pendientes tbody tr:nth-child(even){background:#fafafa}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 4) Cabecera
    st.markdown(
        """
        <div class="gradient-header"><h2>📊 Dashboard AAFF&nbsp;CRM</h2></div>
        """,
        unsafe_allow_html=True,
    )

    # 5) Buscador GPT
    st.markdown("### 🔍 Búsqueda")
    consulta = st.text_input("Escribe lo que quieres buscar…")
    if consulta:
        respuesta, df_res = responder_consulta(df, consulta)
        if not df_res.empty:
            st.success(respuesta)
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 Descargar resultados",
                               df_res.to_csv(index=False).encode("utf-8"),
                               file_name="resultados.csv",
                               mime="text/csv")
        else:
            st.info(respuesta)

    # 6) Filtros rápidos
    nombre_usuario = st.session_state.get("nombre_colaborador", "")
    es_admin = nombre_usuario in ["Ivan Manrique", "SUPER ADMIN"]

    with st.expander("🔍 Filtros", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        # Mes
        meses = ["Todos"] + sorted(df["MES AÑO"].dropna().unique(), reverse=True)
        mes   = c1.selectbox("Mes", meses)
        # Tipo
        tipo  = c2.selectbox("Tipo contrato",
                             ["Todos"] + sorted(df["TIPO CONTRATO"].dropna().unique()))
        # Comercializadora
        com   = c3.selectbox("Comercializadora",
                             ["Todos"] + sorted(df["COMERCIALIZADORA"].dropna().unique()))
        # Usuario
        usr   = c4.selectbox("Usuario",
                             ["Todos"] + sorted(df["USUARIO"].dropna().unique()))

    # Aplico filtros
    df_f = df.copy()
    if mes  != "Todos": df_f = df_f[df_f["MES AÑO"] == mes]
    if tipo != "Todos": df_f = df_f[df_f["TIPO CONTRATO"] == tipo]
    if com  != "Todos": df_f = df_f[df_f["COMERCIALIZADORA"] == com]
    if usr  != "Todos": df_f = df_f[df_f["USUARIO"] == usr]

    # 7) KPIs
    tot_cli  = df_f["CLIENTE"].nunique()
    tot_cups = df_f["CUPS"].nunique()
    contratos= len(df_f)
    com_mes  = df_f["Comision" if es_admin else "Comision COLABORADOR"].sum()
    com_col  = df_f["Comision COLABORADOR"].sum()
    media_c  = (df_f[df_f["TIPO CONTRATO"] != "Renovación Tácita"]
                ["Comision" if es_admin else "Comision COLABORADOR"].mean())

    k1,k2,k3,k4 = st.columns(4)
    tarjeta(k1, "kpi-blue",   "fa-users",            "Total clientes", tot_cli)
    tarjeta(k2, "kpi-orange", "fa-bolt",             "CUPS únicos",    tot_cups)
    tarjeta(k3, "kpi-green",  "fa-file-circle-plus", "Contratos",      contratos)
    tarjeta(k4, "kpi-red",    "fa-coins",            "Comisiones (€)", f"{com_mes:,.2f}")

    k5,k6 = st.columns(2)
    tarjeta(k5, "kpi-red",   "fa-sack-dollar", "Comisión colaborador", f"{com_col:,.2f}")
    tarjeta(k6, "kpi-green", "fa-chart-line",  "Media comisión",       f"{media_c:,.2f}")

    # 8) CONTRATOS PENDIENTES (tabla bonita)
    pendientes = df_f[~df_f["ESTADO"].isin(["Baja", "Activado"])]

    with st.expander(f"📌 Contratos pendientes de cerrar: {len(pendientes)}",
                     expanded=True):
        if pendientes.empty:
            st.success("✔️ No hay contratos pendientes, ¡genial!")
        else:
            for est in sorted(pendientes["ESTADO"].dropna().unique()):
                df_est  = pendientes[pendientes["ESTADO"] == est]
                vista   = df_est[["CLIENTE","CUPS","COMERCIALIZADORA","TARIFA"]] \
                          .rename(columns={
                              "CLIENTE":"Cliente","CUPS":"CUPS",
                              "COMERCIALIZADORA":"Comercializadora","TARIFA":"Tarifa"
                          })

                st.markdown(f"### 🔄 {est} ({len(vista)})")

                # → convertimos la vista a HTML sin índice
                st.markdown(vista.to_html(index=False,
                                          classes="tabla-pendientes"),
                            unsafe_allow_html=True)

                st.download_button(f"⬇️ Descargar {est}",
                                   data=df_est.to_csv(index=False).encode("utf-8"),
                                   file_name=f"contratos_{est.lower().replace(' ','_')}.csv",
                                   mime="text/csv",
                                   key=f"btn_{est}")

    # 9) ÚLTIMOS 5 CONTRATOS ACTIVADOS
        # 10) ÚLTIMOS 5 CONTRATOS ACTIVADOS
    ultimos = (
        df if es_admin else df[df["USUARIO"] == nombre_usuario]
    ).sort_values("FECHA ACTIVACION", ascending=False).head(5)

    with st.expander("🕓 Últimos 5 contratos activados"):
        for _, row in ultimos.iterrows():
            fecha = (
                row["FECHA ACTIVACION"].strftime("%d/%m/%Y")
                if pd.notnull(row["FECHA ACTIVACION"]) else "Sin fecha"
            )
            row_html = f"""
            <div style='padding:1rem;margin-bottom:10px;border:1px solid #eee;
                        border-radius:10px;'>
              <strong>🧾 Cliente:</strong> {row["CLIENTE"]}<br>
              <strong>📅 Fecha:</strong> {fecha}<br>
              <strong>🏢 Comercializadora:</strong> {row["COMERCIALIZADORA"]}<br>
              <strong>🏷️ Tarifa:</strong> {row["TARIFA"]}<br>
              <strong>🔁 Estado:</strong> {row["ESTADO"]}<br>
              <strong>🔌 CUPS:</strong> {row["CUPS"]}
            </div>
            """
            st.markdown(row_html, unsafe_allow_html=True)

