# modules/configuracion.py
# ============================================================================
# CONFIGURACIÓN DEL SISTEMA - PERSISTENCIA EN BD Y RECARGA DINÁMICA
# Versión robustecida: recarga sin reiniciar, logging, validaciones
# ============================================================================

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from modules.main_page import show_module_header
from utils.helpers import add_back_button, hash_password
from database.manager import get_db_v2 as get_db

logger = logging.getLogger(__name__)

def show_configuracion():
    try:
        add_back_button(key="back_config")
        show_module_header("⚙️ Configuración", "Personalización del sistema ERP")
        st.markdown('<div class="module-content">', unsafe_allow_html=True)

        tab1, tab_tiendas, tab2, tab3 = st.tabs(["General", "Tiendas", "Usuarios", "Seguridad"])

        # =========================================================================
        # TAB 1 – CONFIGURACIÓN GENERAL (recarga dinámica)
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
                try:
                    db.guardar_config("zona_horaria", zona)
                    db.guardar_config("moneda", moneda)
                    db.guardar_config("idioma", idioma)
                    db.guardar_config("formato_fecha", formato_fecha)
                    db.guardar_config("decimales", decimales)
                    db.guardar_config("separador_miles", separador_miles)
                    st.success("✅ Configuración guardada exitosamente")
                    # Recargar dinámicamente (sin reiniciar) - forzar rerun
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
                    logger.exception(e)

        # =========================================================================
        # TAB TIENDAS – GESTIÓN DE TIENDAS Y GENERACIÓN DE USUARIOS
        # =========================================================================
        with tab_tiendas:
            st.header("Gestión de Tiendas")
            db = get_db()
            tiendas_docs = db.find("tiendas")
            df_tiendas = pd.DataFrame(tiendas_docs)
            if not df_tiendas.empty:
                st.dataframe(df_tiendas[["Empresa", "Destino", "Nombre de Tienda", "Contacto", "Dirección", "Teléfono"]], use_container_width=True)
            else:
                st.info("No hay tiendas registradas.")
            
            with st.expander("➕ Agregar Nueva Tienda"):
                with st.form("form_tienda"):
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        n_empresa = st.text_input("Empresa (ej. Aeropostale)")
                        n_origen = st.text_input("Origen (ej. MATRIZ)")
                        n_destino = st.text_input("Ciudad/Destino (ej. QUITO)")
                        n_nombre = st.text_input("Nombre de Tienda")
                    with col_t2:
                        n_contacto = st.text_input("Contacto")
                        n_dir = st.text_input("Dirección")
                        n_tel = st.text_input("Teléfono")
                    
                    if st.form_submit_button("Guardar Tienda"):
                        if n_empresa and n_destino and n_nombre:
                            db.insert("tiendas", {
                                "Empresa": n_empresa,
                                "Origen": n_origen,
                                "Destino": n_destino,
                                "Nombre de Tienda": n_nombre,
                                "Contacto": n_contacto,
                                "Dirección": n_dir,
                                "Teléfono": n_tel
                            })
                            st.success(f"Tienda {n_nombre} agregada.")
                            st.rerun()
                        else:
                            st.error("Campos Empresa, Ciudad y Nombre son obligatorios.")

            st.divider()
            st.subheader("Generar Usuarios de Tiendas")
            st.write("Genera cuentas de usuario únicas para cada tienda que no tenga una.")
            if st.button("Generar Usuarios para Tiendas", type="primary"):
                import string
                import random
                import re
                
                users = db.find("users")
                existing_usernames = [u.get("username") for u in users]
                
                generados = []
                for t in tiendas_docs:
                    tienda_name = t.get("Nombre de Tienda")
                    if not tienda_name:
                        continue
                    clean_name = re.sub(r'[^a-zA-Z0-9]', '', tienda_name).lower()
                    username = f"t_{clean_name}"
                    
                    if username not in existing_usernames:
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                        db.insert("users", {
                            "username": username,
                            "role": "Tienda",
                            "password": hash_password(password),
                            "name": tienda_name,
                            "assigned_store": tienda_name,
                            "_created": datetime.utcnow()
                        })
                        generados.append({"Tienda": tienda_name, "Usuario": username, "Contraseña": password})
                        existing_usernames.append(username)
                
                if generados:
                    st.success(f"Se generaron {len(generados)} usuarios nuevos. **Guarda estas contraseñas:**")
                    st.dataframe(pd.DataFrame(generados), use_container_width=True)
                else:
                    st.info("Todas las tiendas ya tienen un usuario asignado.")

        # =========================================================================
        # TAB 2 – GESTIÓN DE USUARIOS
        # =========================================================================
        with tab2:
            st.header("Gestión de Usuarios")
            db = get_db()
            usuarios = db.find("users")
            df_usuarios = pd.DataFrame(usuarios)
            if not df_usuarios.empty and "username" in df_usuarios.columns and "role" in df_usuarios.columns:
                st.dataframe(df_usuarios[["username", "role", "name"]], use_container_width=True)
            else:
                st.info("No hay usuarios registrados.")

            with st.form("form_usuario"):
                st.subheader("Agregar Nuevo Usuario")
                nuevo_usuario = st.text_input("Nombre de usuario")
                nueva_contrasena = st.text_input("Contraseña", type="password")
                rol = st.selectbox("Rol", ["Administrador", "Logística", "Ventas", "Bodega", "Tienda"])
                if st.form_submit_button("➕ Agregar Usuario"):
                    if nuevo_usuario and nueva_contrasena:
                        try:
                            db.insert("users", {
                                "username": nuevo_usuario,
                                "role": rol,
                                "password": hash_password(nueva_contrasena),
                                "name": nuevo_usuario,
                                "_created": datetime.utcnow()
                            })
                            st.success(f"✅ Usuario {nuevo_usuario} agregado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    else:
                        st.error("Completa todos los campos.")

        # =========================================================================
        # TAB 3 – SEGURIDAD (cambio de contraseña)
        # =========================================================================
        with tab3:
            st.header("Configuración de Seguridad")

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
                            # Forzar re-login (opcional)
                            st.info("Recomendamos cerrar sesión e iniciar nuevamente.")

            st.subheader("🔒 Configuración de Sesión")
            st.slider("Tiempo de inactividad (minutos)", 5, 120, 30, disabled=True)
            st.slider("Máximo de intentos fallidos", 3, 10, 5, disabled=True)

            if st.button("🔒 Aplicar Configuración de Seguridad"):
                st.info("Las opciones avanzadas de seguridad aún no están integradas.")

        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error general en configuración: {e}")
        logger.exception(e)
