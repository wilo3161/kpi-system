import re

with open("modules/equipo.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace the col_form logic and the admin report generation logic.

# Find the start of `with col_form:`
start_idx = content.find("        with col_form:")
# Find the start of `    st.markdown('</div>', unsafe_allow_html=True)`
end_idx = content.find("    st.markdown('</div>', unsafe_allow_html=True)")

new_block = """        with col_form:
            from datetime import time as dt_time
            from datetime import datetime
            
            now = datetime.now()
            hora_actual = now.time()
            hora_limite = dt_time(20, 0)
            
            # Consultar última emisión del reporte
            estado_cierre = local_db.find_one("estado_sistema", {"id": "cierre_reporte"})
            if not estado_cierre:
                ultima_emision_dt = datetime(1970, 1, 1)
            else:
                ultima_emision_dt = datetime.fromisoformat(estado_cierre.get("ultima_emision", "1970-01-01T00:00:00"))
            
            bloqueado = False
            if not is_admin:
                if hora_actual >= hora_limite:
                    limite_hoy = datetime.combine(now.date(), hora_limite)
                    # Si ya son pasadas las 20:00 y no se ha emitido el reporte después de las 20:00 de hoy
                    if ultima_emision_dt < limite_hoy:
                        bloqueado = True
            
            if bloqueado:
                st.error("⏰ El horario de registro ha finalizado (corte a las 20:00). Estará habilitado nuevamente una vez que el Administrador emita el reporte de hoy.")
            else:
                if ahora.hour >= 20:
                    st.info("🌙 Registro habilitado para el día de MAÑANA.")
                    
                with st.form("form_actividades"):
                    st.subheader("Ingresar Actividad")
                    empleado = st.selectbox("Selecciona tu nombre", [""] + miembros_ingreso)
                    actividad = st.text_area("Describe tus actividades (ej. Transferencias: Ejecución de transferencias de 2,000 prendas...)", height=150)
                    
                    if st.form_submit_button("Guardar Información", use_container_width=True):
                        if empleado and actividad:
                            local_db.insert("actividades_diarias", {
                                "fecha": fecha_hoy,
                                "empleado": empleado,
                                "actividad": actividad,
                                "hora_registro": datetime.now().strftime("%H:%M:%S")
                            })
                            st.success(f"✅ Información guardada correctamente para {empleado}.")
                            st.rerun()
                        else:
                            st.error("Por favor, selecciona tu nombre y describe la actividad.")
        
        # SECCIÓN EXCLUSIVA PARA EL ADMINISTRADOR
        if is_admin:
            st.divider()
            st.subheader("📊 Reporte Consolidado (Administrador)")
            
            # El administrador consulta el reporte de HOY, aunque sea pasadas las 20:00
            fecha_consulta = st.date_input("Consultar registros por fecha:", datetime.now().date())
            fecha_str = fecha_consulta.strftime("%Y-%m-%d")
            
            if st.button("Generar Registro", type="primary", use_container_width=True):
                # Registrar que se emitió el reporte para habilitar la plataforma
                from datetime import datetime
                now_str = datetime.now().isoformat()
                estado_cierre = local_db.find_one("estado_sistema", {"id": "cierre_reporte"})
                if estado_cierre:
                    if hasattr(local_db, 'data') and 'estado_sistema' in local_db.data:
                        local_db.data["estado_sistema"] = [x for x in local_db.data["estado_sistema"] if x.get("id") != "cierre_reporte"]
                    else:
                        local_db.delete("estado_sistema", {"id": "cierre_reporte"})
                local_db.insert("estado_sistema", {"id": "cierre_reporte", "ultima_emision": now_str})
                
                acts_consulta = local_db.find("actividades_diarias", {"fecha": fecha_str})
                if acts_consulta:
                    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    fecha_formateada = f"{fecha_consulta.day:02d} de {meses[fecha_consulta.month]} de {fecha_consulta.year}"
                    
                    reporte = f"Reporte de actividades - {fecha_formateada}\\n\\n"
                    
                    # Agrupar por empleado para mantener todo en un solo bloque por persona
                    acts_por_emp = {}
                    for a in acts_consulta:
                        emp = a.get("empleado", "Desconocido")
                        if emp not in acts_por_emp:
                            acts_por_emp[emp] = []
                        acts_por_emp[emp].append(a.get("actividad", ""))
                    
                    for emp, textos in acts_por_emp.items():
                        reporte += f"{emp}:\\n\\n"
                        for t in textos:
                            reporte += f"{t}\\n\\n"
                    
                    st.code(reporte, language="text")
                else:
                    st.warning(f"Aún no hay actividades registradas para la fecha: {fecha_str}.")

"""

new_content = content[:start_idx] + new_block + content[end_idx:]

with open("modules/equipo.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done patching modules/equipo.py")
