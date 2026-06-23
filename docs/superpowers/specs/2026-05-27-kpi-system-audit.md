# Auditoría y Testing del KPI System — Brainstorming Spec

## 1. Alcance Actual
El usuario solicita probar y detectar posibles fallas o bugs en el ERP "kpi-system" completo.
**Alerta de Alcance:** El ERP consta de múltiples módulos independientes (`logistica`, `recepcion`, `equipo`, `dashboard_kpis`, `auth`, `app.py`, entre otros). Analizar todo de golpe es ineficiente y propenso a pasar por alto bugs profundos. Necesitamos descomponer este proyecto de testing por subsistemas (módulos).

## 2. Refinamiento (Preguntas Socráticas)
- **¿Cuál es el problema real?** Necesitamos asegurar la estabilidad del sistema, evitar caídas de Streamlit, manejar correctamente las conexiones a MongoDB, y verificar que no existan colisiones en `st.session_state`.
- **¿Qué alternativas existen?** 
  - A) Análisis estático (Linter/MyPy)
  - B) Análisis dinámico / unit tests para los procesos críticos (parsing de productos, subida de archivos).
  - C) Revisión manual algorítmica de los flujos de Streamlit (estado y repintado).
- **¿Cuáles son las restricciones?** Las aplicaciones de Streamlit pueden ser difíciles de probar con herramientas unitarias tradicionales. El enfoque debe centrarse en la revisión de arquitectura del estado de la sesión (`st.session_state`), manejo de excepciones, dependencias y seguridad de la base de datos (MongoDB).

## 3. Propuesta de Descomposición (Secciones de Testing)
Se propone dividir el esfuerzo de revisión y debugging en los siguientes "Subsistemas":
1. **Core & Estado (app.py, config):** Revisión de la gestión global de la sesión, enrutamiento y autenticación.
2. **Conexiones y BD (database/):** Verificación de inyecciones, bloqueos y fallos de red en MongoDB.
3. **Módulo de Logística (logistica.py):** Revisión de cargas de archivos, procesamiento de dataframes, y algoritmos de regex para el clasificador textil.
4. **Módulo de Recepción (recepcion.py):** Verificación de generación de PDFs y lógica de confirmación.
5. **Módulo de Equipo y Asistente IA (equipo.py, ai/):** Revisión de integración de APIs externas (DeepSeek) y manejo de errores HTTP.

---
> Esperando validación del humano para proceder con la revisión módulo por módulo.
