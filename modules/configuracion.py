# modules/configuracion.py
import streamlit as st
import pandas as pd
from utils.ui import show_module_header
from utils.helpers import add_back_button, hash_password
from database.manager import get_db_v2 as get_db

def show_configuracion():
    add_back_button(key="back_config")
    show_module_header("⚙️ Configuración", "Personalización del sistema ERP")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["General", "Usuarios", "Seguridad"])

    # =========================================================================
    # TAB 1 – CONFIGURACIÓN GENERAL (ahora persiste en BD)
    # =========================================================================
    with tab1:
        st.header("Configuración General")
        db = get_db()

        # Cargar valores guardados previamente
        zona_guardada = db.leer_config("zona_horaria", "America/Guayaquil")
        moneda_guardada = db.leer_config("moneda", "USD")
        idioma_guardado = db.leer_config("idioma", "Español")
        formato_fecha_guardado = db.leer_config("formato_fecha", "DD/MM/YYYY")
        decimales_guardado = db.leer_config("decimales", 2)
        separador_miles_guardado = db.leer_config("separador_miles", ",")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🌐 Configuración Regional")
            zona = st.selectbox(
                "Zona Horaria",
                ["America/Guayaquil", "UTC", "America/Bogota", "America/Lima"],
                index=0 if zona_guardada == "America/Guayaquil" else 1,
            )
            moneda = st.selectbox(
                "Moneda",
                ["USD", "EUR", "COP"],
                index=0 if moneda_guardada == "USD" else (1 if moneda_guardada == "EUR" else 2),
            )
            idioma = st.selectbox(
                "Idioma",
                ["Español", "Inglés"],
                index=0 if idioma_guardado == "Español" else 1,
            )
        with col2:
            st.subheader("📊 Configuración de Reportes")
            formato_fecha = st.selectbox(
                "Formato de Fecha",
                ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
                index=0 if formato_fecha_guardado == "DD/MM/YYYY" else (1 if formato_fecha_guardado == "MM/DD/YYYY" else 2),
            )
            decimales = st.slider("Decimales", 0, 4, decimales_guardado)
            separador_miles = st.selectbox(
                "Separador de Miles",
                [",", ".", " "],
                index=0 if separador_miles_guardado == "," else (1 if separador_miles_guardado == "." else 2),
            )

        if st.button("💾 Guardar Configuración"):
            db.guardar_config("zona_horaria", zona)
            db.guardar_config("moneda", moneda)
            db.guardar_config("idioma", idioma)
            db.guardar_config("formato_fecha", formato_fecha)
            db.guardar_config("decimales", decimales)
            db.guardar_config("separador_miles", separador_miles)
            st.success("✅ Configuración guardada exitosamente")

    # =========================================================================
    # TAB 2 – GESTIÓN DE USUARIOS
    # =========================================================================
    with tab2:
        st.header("Gestión de Usuarios")
        db = get_db()
        usuarios = db.find("users")
        df_usuarios = pd.DataFrame(usuarios)
        if not df_usuarios.empty and "username" in df_usuarios.columns and "role" in df_usuarios.columns:
            st.dataframe(df_usuarios[["username", "role"]], use_container_width=True)
        else:
            st.info("No hay usuarios registrados.")

        with st.form("form_usuario"):
            st.subheader("Agregar Nuevo Usuario")
            nuevo_usuario = st.text_input("Nombre de usuario")
            nueva_contrasena = st.text_input("Contraseña", type="password")
            rol = st.selectbox("Rol", ["Administrador", "Logística", "Ventas", "Bodega"])
            if st.form_submit_button("➕ Agregar Usuario"):
                if nuevo_usuario and nueva_contrasena:
                    try:
                        db.insert("users", {
                            "username": nuevo_usuario,
                            "role": rol,
                            "password": hash_password(nueva_contrasena),
                        })
                        st.success(f"✅ Usuario {nuevo_usuario} agregado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("Completa todos los campos.")

    # =========================================================================
    # TAB 3 – SEGURIDAD (cambio de contraseña corregido)
    # =========================================================================
    with tab3:
        st.header("Configuración de Seguridad")

        # --- Cambio de contraseña personal ---
        with st.expander("🔐 Cambiar mi contraseña", expanded=False):
            st.markdown("### Actualiza tu contraseña personal")
            current_pwd = st.text_input("Contraseña actual", type="password", key="current_pwd")
            new_pwd = st.text_input("Nueva contraseña", type="password", key="new_pwd")
            confirm_pwd = st.text_input("Confirmar nueva contraseña", type="password", key="confirm_pwd")
            if st.button("Actualizar contraseña"):
                db = get_db()
                username = st.session_state.get("username", "")
                if not username:
                    st.error("No hay sesión activa.")
                else:
                    # Verificar contraseña actual
                    user_data = db.authenticate(username, hash_password(current_pwd))
                    if not user_data:
                        st.error("❌ La contraseña actual es incorrecta.")
                    elif new_pwd != confirm_pwd:
                        st.error("❌ Las contraseñas nuevas no coinciden.")
                    elif len(new_pwd) < 4:
                        st.error("❌ La nueva contraseña debe tener al menos 4 caracteres.")
                    else:
                        new_hash = hash_password(new_pwd)
                        db.update_password(username, new_hash)
                        st.success("✅ Contraseña actualizada correctamente.")
                        # Forzar re-login (opcional, solo información)
                        st.info("Recomendamos cerrar sesión e iniciar nuevamente.")

        # --- Políticas de contraseña (solo visual, como antes) ---
        st.subheader("🔐 Políticas de Contraseña")
        st.slider("Longitud mínima de contraseña", 6, 20, 8, disabled=True)
        st.checkbox("Requerir mayúsculas", True, disabled=True)
        st.checkbox("Requerir números", True, disabled=True)
        st.selectbox("Expiración de contraseña (días)", ["30", "60", "90", "Nunca"], disabled=True)

        st.subheader("🔒 Configuración de Sesión")
        st.slider("Tiempo de inactividad (minutos)", 5, 120, 30, disabled=True)
        st.slider("Máximo de intentos fallidos", 3, 10, 5, disabled=True)

        if st.button("🔒 Aplicar Configuración de Seguridad"):
            st.info("Las opciones avanzadas de seguridad aún no están integradas.")

    st.markdown('</div>', unsafe_allow_html=True)
