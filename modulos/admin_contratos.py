# ── modulos/admin_contratos.py ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from .notion_api import actualizar_contratos_notion

# ▼ Dropdowns
ESTADOS           = ["Cargado", "Enviada CUPS", "Activado", "Baja"]
COMERCIALIZADORAS = ["Endesa", "Repsol", "Naturgy", "Gana Energía"]
COLABORADORES     = ["Ivan Manrique", "Ana", "Pepe"]

# ───────────────────────────────────────────────────────────────────────────
def mostrar_carga_contratos(df_original: pd.DataFrame, database_id: str) -> None:
    """Pantalla admin para importar/editar contratos y subirlos a Notion."""
    st.header("📝 Carga y edición de contratos (solo Admin)")

    # ---------- Upload o nueva fila
    col_up, col_new = st.columns([3, 1])
    archivo = col_up.file_uploader("📤 Importar Excel", type=["xlsx"])
    if col_new.button("➕ Añadir fila"):
        df_original = df_original.append(
            {"CLIENTE": "", "CUPS": "", "ESTADO": "", "COMERCIALIZADORA": "",
             "TARIFA": "", "USUARIO": "", "Comision": 0.0,
             "Comision COLABORADOR": 0.0, "FECHA ACTIVACION": ""},
            ignore_index=True,
        )
    if archivo:
        df_original = pd.read_excel(archivo)

    # ---------- Ag-Grid config
    req_js = JsCode("function(p){if(!p.value){return {backgroundColor:'#ffcccc'}}}")

    gb = GridOptionsBuilder.from_dataframe(df_original)
    gb.configure_default_column(editable=True, resizable=True)

    gb.configure_column("CLIENTE", pinned="left", cellStyle=req_js)
    gb.configure_column("CUPS",    cellStyle=req_js)

    # dropdowns
    gb.configure_column("ESTADO",
        cellEditor="agSelectCellEditor",
        cellEditorParams={"values": ESTADOS},
        cellStyle=req_js)
    gb.configure_column("COMERCIALIZADORA",
        cellEditor="agSelectCellEditor",
        cellEditorParams={"values": COMERCIALIZADORAS})
    gb.configure_column("USUARIO",
        cellEditor="agSelectCellEditor",
        cellEditorParams={"values": COLABORADORES})

    # fechas y números
    gb.configure_column("FECHA ACTIVACION",
        type=["dateColumnFilter", "customDateTimeFormat"],
        custom_format_string="yyyy-MM-dd")
    gb.configure_column("Comision",             type=["numericColumn"])
    gb.configure_column("Comision COLABORADOR", type=["numericColumn"])

    # extras “modo Excel”
    gb.configure_grid_options(
        enableRangeSelection=True,
        enableFillHandle=True,
        undoRedoCellEditing=True,
        sideBar=True,
        rowSelection="multiple",
        statusBar={
            "statusPanels": [
                {"statusPanel": "agAggregationComponent",
                 "statusPanelParams": {"aggregationFuncs": ["sum","count","avg"]}}
            ]
        },
    )

    grid = AgGrid(
        df_original,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=520,
    )
    df_editado = pd.DataFrame(grid["data"])

    # ---------- Botones
    col_save, col_dl = st.columns(2)

    if col_save.button("💾 Guardar cambios en Notion"):
        with st.spinner("Actualizando…"):
            ok, errores = actualizar_contratos_notion(df_editado, database_id)
        if ok:
            st.success("✅ Actualizado en Notion.")
        else:
            st.error("❌ Fallos en algunas filas.")
            st.write(errores)

    col_dl.download_button(
        "⬇️ Descargar Excel",
        data=df_editado.to_excel(index=False, engine="openpyxl"),
        file_name="contratos_editados.xlsx",
    )
