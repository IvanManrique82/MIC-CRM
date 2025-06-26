
import pandas as pd

def validar_usuario(usuario, contraseña, df_usuarios):
    usuario = usuario.strip().lower()
    contraseña = str(contraseña).strip()

    fila = df_usuarios[df_usuarios["USUARIO"].str.lower().str.strip() == usuario]

    if not fila.empty:
        clave_correcta = str(fila.iloc[0]["CONTRASEÑA"]).strip()
        if clave_correcta == contraseña:
            return fila.iloc[0]["NOMBRE DE COLABORADOR"], fila.iloc[0]["ROL"]
    return None, None
