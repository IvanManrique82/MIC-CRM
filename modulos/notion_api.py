# ── modulos/notion_api.py ────────────────────────────────────────────────────
import os
import json
import pandas as pd
import requests
from typing import Tuple, List

# 1) Configuración ───────────────────────────────────────────────────────────
NOTION_TOKEN   = os.getenv("NOTION_TOKEN", "TU_TOKEN_AQUÍ")
NOTION_VERSION = "2022-06-28"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

# Ajusta columnas según tu base de datos
TIPOS_DEFECTO = {
    "title":       ["CLIENTE"],
    "rich_text":   ["CUPS", "COMERCIALIZADORA", "TARIFA", "ESTADO", "USUARIO"],
    "number":      ["Comision", "Comision COLABORADOR"],
    "date":        ["FECHA ACTIVACION"],
}

# ───────────────── LECTURA ──────────────────────────────────────────────────
def obtener_datos_notion(token: str, database_id: str) -> pd.DataFrame:
    """Lee toda la base y devuelve DataFrame con columna NOTION_ID."""
    url     = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    registros, has_more, cursor = [], True, None
    while has_more:
        body = {"start_cursor": cursor} if cursor else {}
        r    = requests.post(url, headers=headers, json=body)
        if r.status_code != 200:
            print("❌ Error Notion:", r.text)
            return pd.DataFrame()

        data      = r.json()
        has_more  = data.get("has_more", False)
        cursor    = data.get("next_cursor", None)

        for page in data.get("results", []):
            fila          = _props_to_dict(page["properties"])
            fila["NOTION_ID"] = page["id"]
            registros.append(fila)

    return pd.DataFrame(registros)


def _props_to_dict(props: dict) -> dict:
    """Convierte propiedades Notion → dict plano."""
    d = {}
    for k, v in props.items():
        t = v.get("type")
        if t == "title":
            d[k] = v[t][0]["plain_text"] if v[t] else ""
        elif t == "rich_text":
            d[k] = v[t][0]["plain_text"] if v[t] else ""
        elif t == "number":
            d[k] = v[t]
        elif t == "select":
            d[k] = v[t]["name"] if v[t] else ""
        elif t == "multi_select":
            d[k] = ", ".join(opt["name"] for opt in v[t]) if v[t] else ""
        elif t == "date":
            d[k] = v[t]["start"] if v[t] else ""
        elif t == "checkbox":
            d[k] = v[t]
        else:
            d[k] = str(v.get(t))
    return d

# ───────────────── ESCRITURA / ACTUALIZACIÓN ────────────────────────────────
def actualizar_contratos_notion(
    df: pd.DataFrame, database_id: str
) -> Tuple[bool, List[str]]:
    """
    Si la fila trae NOTION_ID → PATCH; si no, crea página nueva.
    Devuelve (ok_general, lista_errores).
    """
    errores: List[str] = []

    for _, fila in df.iterrows():
        page_id = str(fila.get("NOTION_ID", "")).strip()
        payload = {"properties": _fila_a_props(fila)}

        if page_id:   # PATCH
            url  = f"https://api.notion.com/v1/pages/{page_id}"
            resp = requests.patch(url, headers=HEADERS, json=payload)
        else:         # POST
            payload["parent"] = {"database_id": database_id}
            url  = "https://api.notion.com/v1/pages"
            resp = requests.post(url, headers=HEADERS, json=payload)

        if resp.status_code not in (200, 201):
            errores.append(f"{fila.get('CLIENTE','(sin cliente)')}: {resp.text[:120]}")

    return len(errores) == 0, errores


def _fila_a_props(row: pd.Series) -> dict:
    """
    Convierte una fila DataFrame → propiedades Notion usando TIPOS_DEFECTO.
    """
    props = {}

    # recorre por tipo y columnas asociadas
    for tipo, cols in TIPOS_DEFECTO.items():
        for col in cols:
            if col not in row:
                continue
            val = row[col]

            if tipo == "title":
                props[col] = {"title": [{"text": {"content": str(val)}}]}

            elif tipo == "rich_text":
                props[col] = {"rich_text": [{"text": {"content": str(val)}}]}

            elif tipo == "number":
                num = None if pd.isna(val) or val == "" else float(val)
                props[col] = {"number": num}

            elif tipo == "date":
                fecha = ""
                if pd.notna(val) and val != "":
                    fecha = str(val)[:10]           # YYYY-MM-DD
                props[col] = {"date": {"start": fecha} if fecha else None}

            # añade aquí 'select', 'checkbox', etc. si los tienes

    return props
