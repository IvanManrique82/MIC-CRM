import streamlit as st
import pandas as pd


# ═════════════════════════  LOGIN FULL-SCREEN  ═════════════════════════
def mostrar_login_pantalla_completa(usuarios_df: pd.DataFrame) -> None:
    """Pantalla de acceso con foto izquierda + panel formulario derecha."""
    st.markdown(
        """
        <style>
        /* Ocultamos sidebar y header */
        [data-testid="stSidebar"], header {display:none;}
        body{margin:0!important;}

        /* Wrapper flex 55/45 */
        .login-wrapper{
            position:fixed; inset:0;
            width:100vw; height:100vh;
            display:flex;
        }
        .login-left{
            flex:55;
            background:url('assets/login_bg.jpg') center/cover no-repeat;
        }
        .login-right{
            flex:45;
            backdrop-filter:blur(4px);
            background:rgba(255,255,255,.66);
            display:flex; justify-content:center; align-items:center;
        }
        .login-box{width:80%; max-width:430px;}
        .login-box img{width:210px; margin:auto; display:block;}

        /* Inputs y botón */
        .stTextInput input, .stPassword input{background:#f3f6fa;border-radius:6px;}
        .stButton>button{
            background:#d71920;color:#fff;font-weight:600;
            border:none;border-radius:6px;height:42px;
        }
        .stButton>button:hover{background:#b9151c;}
        .forgot-link{text-align:right;font-style:italic;color:#666;}
        </style>

        <!-- Estructura -->
        <div class="login-wrapper">
            <div class="login-left"></div>
            <div class="login-right">
                <div class="login-box">
        """,
        unsafe_allow_html=True,
    )

    # ---------- FORMULARIO STREAMLIT ----------
    st.image("assets/logo.png")
    st.subheader("Pantalla de Acceso")

    usuario = st.text_input("Usuario", placeholder="ej: ivan", key="lg_user")
    clave   = st.text_input("Contraseña", type="password", key="lg_pass")

    if st.button("Iniciar sesión", use_container_width=True, key="lg_btn"):
        fila = usuarios_df[
            (usuarios_df["USUARIO"].str.lower().str.strip() == usuario.strip().lower()) &
            (usuarios_df["CONTRASEÑA"].astype(str).str.strip() == str(clave).strip())
        ]
        if not fila.empty:
            st.session_state.logueado           = True
            st.session_state.nombre_colaborador = fila.iloc[0]["NOMBRE DE COLABORADOR"]
            st.session_state.rol                = fila.iloc[0]["ROL"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.markdown(
        """
        <p class="forgot-link">¿Olvidó su contraseña?</p>
                </div>  <!-- /login-box -->
            </div>      <!-- /login-right -->
        </div>          <!-- /login-wrapper -->
        """,
        unsafe_allow_html=True,
    )


# ═════════════════════════  SIDEBAR NORMAL  ═════════════════════════════
def mostrar_sidebar(usuarios_df: pd.DataFrame) -> None:
    """Menú lateral cuando el usuario ya está logueado."""
    st.sidebar.image("assets/logo.png", use_container_width=True)
    st.sidebar.success(f"👤 {st.session_state.nombre_colaborador} ({st.session_state.rol})")

    if "seccion" not in st.session_state:
        st.session_state.seccion = "Dashboard"

    st.sidebar.markdown("## Menú")
    st.session_state.seccion = st.sidebar.radio(
        "Selecciona una sección:",
        ["Dashboard", "Clientes", "Facturas"],
        index=["Dashboard", "Clientes", "Facturas"].index(st.session_state.seccion),
    )

    if st.sidebar.button("Cerrar sesión"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
