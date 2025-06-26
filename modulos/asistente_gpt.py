import streamlit as st
import pandas as pd
import difflib
from openai import OpenAI
import os

# Inicializa el cliente OpenAI con tu clave personal
client = OpenAI(api_key="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")

def cargar_datos(path):
    df = pd.read_csv(path)
    df.columns = [col.strip().upper() for col in df.columns]
    columnas_a_omitir = [
        'OBSERVACIONES CONTRATO', 'ESTUDIO', 'FACTURA',
        'CONTRATO', 'COMENTARIOS', 'SEGMENTO'
    ]
    df = df[[col for col in df.columns if col not in columnas_a_omitir and not col.startswith('UNNAMED')]]
    return df

def buscar_contratos_por_mes(df, mes):
    mes = mes.lower()
    if "MES AÑO" in df.columns:
        return df[df["MES AÑO"].str.lower().str.contains(mes, na=False)]
    return pd.DataFrame()

def buscar_por_cliente(df, nombre):
    clientes = df['CLIENTE'].dropna().unique()
    coincidencia = difflib.get_close_matches(nombre.upper(), clientes, n=1, cutoff=0.5)
    if coincidencia:
        return df[df['CLIENTE'] == coincidencia[0]], coincidencia[0]
    return pd.DataFrame(), None

def resumen_por_mes(df, mes):
    contratos = buscar_contratos_por_mes(df, mes)
    total = len(contratos)
    resumen = f"En {mes.capitalize()} tienes un total de {total} contratos activos."
    return resumen, contratos

def usar_asistente_gpt(df, pregunta):
    columnas_a_excluir = [
        "Representante", "DNI REPRESENTANTE", "EMAIL", "MOVIL", "P1", "P2", "P3",
        "P4", "P5", "P6", "DIRECCION DE SUMINISTRO", "OBSERVACIONES CONTRATO",
        "COMENTARIOS", "CONTRATO", "ESTUDIO", "FACTURA"
    ]
    columnas_utiles = [col for col in df.columns if col not in columnas_a_excluir][:15]
    df_reducido = df[columnas_utiles].copy().head(100)

    csv_data = df_reducido.to_csv(index=False)

    prompt = f"""
Eres un asistente que responde preguntas sobre datos de contratos eléctricos.
Analiza el siguiente CSV y responde de forma precisa a la consulta que te indiquen:

CSV:
{csv_data}

Consulta: {pregunta}
Responde de forma concisa y clara.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asesor energético profesional. Responde de forma clara, útil y con lenguaje sencillo. Si la consulta se refiere a un cliente, revisa el nombre y responde con su información concreta. Si no hay coincidencias claras, responde que no hay datos suficientes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return "🔮 Usando inteligencia GPT:\n" + response.choices[0].message.content, df_reducido
    except Exception as e:
        return f"❌ Error al conectar con GPT: {e}", pd.DataFrame()

def responder_consulta(df, pregunta):
    pregunta = pregunta.lower().strip()

    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

    if 'cuantos contratos' in pregunta and any(mes in pregunta for mes in meses):
        for mes in meses:
            if mes in pregunta:
                resumen, contratos = resumen_por_mes(df, mes)
                return "🧮 Resultado directo:\n" + resumen, contratos

    if 'cuantos contratos tiene' in pregunta:
        nombre = pregunta.split('cuantos contratos tiene')[-1].strip()
        resultado, cliente = buscar_por_cliente(df, nombre)
        if not resultado.empty:
            total = len(resultado)
            return f"🧮 Resultado directo:\n{cliente} tiene un total de {total} contratos registrados.", resultado
        else:
            return f"No se encontraron contratos para {nombre}.", pd.DataFrame()

    if 'cif' in pregunta:
        nombre = pregunta.split('cif')[-1].strip()
        resultado, cliente = buscar_por_cliente(df, nombre)
        if not resultado.empty:
            return f"🧮 Resultado directo:\nEl CIF de {cliente} es: {resultado['CIF/DNI'].iloc[0]}", resultado
        else:
            return f"No tengo información sobre el CIF de {nombre}.", pd.DataFrame()

    if 'dni' in pregunta:
        nombre = pregunta.split('dni')[-1].strip()
        resultado, cliente = buscar_por_cliente(df, nombre)
        if not resultado.empty and 'DNI REPRESENTANTE' in resultado.columns:
            return f"🧮 Resultado directo:\nEl DNI de {cliente} es: {resultado['DNI REPRESENTANTE'].iloc[0]}", resultado
        else:
            return f"No tengo información sobre el DNI de {nombre}.", pd.DataFrame()

    if 'iban' in pregunta:
        nombre = pregunta.split('iban')[-1].strip()
        resultado, cliente = buscar_por_cliente(df, nombre)
        if not resultado.empty and 'IBAN' in resultado.columns:
            return f"🧮 Resultado directo:\nEl IBAN de {cliente} es: {resultado['IBAN'].iloc[0]}", resultado
        else:
            return f"No tengo información sobre el IBAN de {nombre}.", pd.DataFrame()

    if 'cups' in pregunta:
        nombre = pregunta.split('cups')[-1].strip()
        resultado, cliente = buscar_por_cliente(df, nombre)
        if not resultado.empty:
            cups_col = next((col for col in resultado.columns if 'CUPS' in col.upper()), None)
            if cups_col:
                return f"🧮 Resultado directo:\nEl CUPS de {cliente} es: {resultado[cups_col].iloc[0]}", resultado
        return f"No tengo información sobre el CUPS de {nombre}.", pd.DataFrame()

    return usar_asistente_gpt(df, pregunta)

def mostrar_chat_gpt():
    st.title("🤖 CHAT GPT")

    ruta_csv = "CRM BASE DE DATOS 2025 2112a72faa1f800e9de5d5a6a2a7a003_all.csv"
    df = cargar_datos(ruta_csv)

    st.markdown("Haz preguntas sobre tus contratos: por mes, nombre, comisión, tipo, estado, etc.")

    pregunta = st.text_input("Escribe lo que quieres buscar... (ej. contratos con más de 10000 kWh en 2024)")

    if pregunta:
        respuesta, contratos_usados = responder_consulta(df, pregunta)
        st.info(respuesta)

        if not contratos_usados.empty:
            with st.expander("📄 Ver contratos usados para esta respuesta"):
                st.dataframe(contratos_usados)
                st.download_button("📅 Descargar", contratos_usados.to_csv(index=False).encode('utf-8'), file_name="contratos_filtrados.csv", mime="text/csv")

__all__ = ["responder_consulta"]

