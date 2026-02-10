# 👔 AEROPOSTALE ERP - Sistema de Gestión Empresarial

Sistema ERP completo para el Centro de Distribución de AEROPOSTALE Ecuador. Desarrollado con Streamlit para proporcionar una interfaz moderna, intuitiva y profesional para la gestión de operaciones logísticas, financieras y administrativas.

![Version](https://img.shields.io/badge/version-4.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red)
![License](https://img.shields.io/badge/license-Proprietary-orange)

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Módulos del Sistema](#-módulos-del-sistema)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías](#-tecnologías)
- [Desarrollo](#-desarrollo)
- [Autor](#-autor)

## ✨ Características

- 🎨 **Interfaz Moderna**: Diseño profesional con animaciones y transiciones suaves
- 📊 **Dashboard en Tiempo Real**: Métricas KPI actualizadas constantemente
- 💰 **Reconciliación Financiera**: Sistema avanzado de conciliación V8
- 📧 **IA para Emails**: Auditoría inteligente de correos y novedades
- 📦 **Gestión Logística**: Control completo de transferencias y distribución
- 👥 **Administración de Personal**: Gestión del equipo de trabajo
- 🚚 **Generador de Guías**: Sistema de envíos con códigos QR
- 📋 **Control de Inventario**: Gestión de stock en tiempo real
- 📈 **Reportes Avanzados**: Análisis ejecutivos y estadísticas
- ⚙️ **Configuración Flexible**: Personalización completa del sistema

## 🎯 Módulos del Sistema

### 1. 📊 Dashboard de KPIs
Visualización en tiempo real de las métricas clave del Centro de Distribución:
- Productividad diaria
- Eficiencia operativa
- Costos logísticos
- Personal activo
- Gráficos interactivos con Plotly

### 2. 💰 Reconciliación Financiera V8
Sistema avanzado de conciliación entre facturas y manifiestos:
- Importación de archivos Excel/CSV
- Clasificación automática de tiendas
- Detección de diferencias
- Generación de reportes
- Lógica V8 con reglas específicas

### 3. 📧 Email Wilo AI
Auditoría inteligente de correos electrónicos:
- Conexión con servidores IMAP
- Clasificación automática de novedades
- Detección de faltantes, sobrantes y daños
- Priorización por urgencia
- Generación de respuestas automáticas

### 4. 📦 Dashboard de Transferencias
Control logístico completo:
- Distribución por categorías
- Seguimiento de estados
- Análisis de tiempos
- Gráficos de distribución
- Exportación de reportes

### 5. 👥 Gestión de Trabajadores
Administración del equipo:
- Estructura organizacional
- Registro de personal
- Estadísticas de equipo
- Control de asistencia
- Evaluación de desempeño

### 6. 🚚 Generador de Guías
Sistema de envíos con QR:
- Generación de guías PDF
- Códigos QR para seguimiento
- Impresión directa
- Envío por email
- Historial de envíos

### 7. 📋 Control de Inventario
Gestión de stock (en desarrollo):
- Control de existencias
- Alertas de stock bajo
- Valorización de inventario
- Trazabilidad de productos
- Auditorías automáticas

### 8. 📈 Reportes Avanzados
Análisis ejecutivos (en desarrollo):
- Reportes operacionales
- Reportes financieros
- Reportes logísticos
- Exportación a Excel/PDF
- Dashboards personalizables

### 9. ⚙️ Configuración
Personalización del sistema:
- Configuración general
- Gestión de usuarios
- Seguridad y permisos
- Temas y preferencias
- Logs de actividad

## 🚀 Instalación

### Prerrequisitos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/wilo3161/kpi-system.git
cd kpi-system
```

2. **Crear entorno virtual** (recomendado)
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación**
```bash
streamlit run Home.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📖 Uso

### Navegación Principal

1. **Página de Inicio**: Accede desde `Home.py` para ver todos los módulos disponibles
2. **Selecciona un módulo**: Haz clic en cualquier tarjeta de módulo
3. **Navegación lateral**: Usa el menú lateral para cambiar entre módulos

### Carga de Datos

- **Archivos Excel/CSV**: Arrastra y suelta o usa el botón de carga
- **Datos de demostración**: Activa el checkbox "Usar datos de demostración"
- **Configuración**: Ajusta las columnas según tu estructura de datos

### Exportación de Resultados

- **Excel**: Botón "Exportar a Excel"
- **PDF**: Botón "Generar PDF"
- **Impresión**: Usa el botón de impresión directa

## 📁 Estructura del Proyecto

```
kpi-system/
│
├── Home.py                          # Página principal
│
├── pages/                           # Módulos del sistema
│   ├── 1_📊_Dashboard_KPIs.py
│   ├── 2_💰_Reconciliación_V8.py
│   ├── 3_📧_Email_Wilo_AI.py
│   ├── 4_📦_Dashboard_Transferencias.py
│   ├── 5_👥_Trabajadores.py
│   ├── 6_🚚_Generar_Guías.py
│   ├── 7_📋_Inventario.py
│   ├── 8_📈_Reportes.py
│   └── 9_⚙️_Configuración.py
│
├── utils/                           # Utilidades compartidas
│   ├── __init__.py
│   ├── helpers.py                   # Funciones auxiliares
│   ├── database.py                  # Base de datos local
│   └── styles.py                    # Estilos CSS
│
├── assets/                          # Recursos estáticos
│   ├── css/                         # Archivos CSS adicionales
│   └── images/                      # Imágenes y logos
│
├── data/                            # Datos de ejemplo
├── config/                          # Archivos de configuración
│
├── requirements.txt                 # Dependencias del proyecto
├── README.md                        # Documentación
└── .gitignore                       # Archivos ignorados por Git
```

## 🛠️ Tecnologías

### Backend
- **Python 3.9+**: Lenguaje principal
- **Streamlit**: Framework web
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos

### Visualización
- **Plotly**: Gráficos interactivos
- **Matplotlib**: Gráficos estáticos
- **Seaborn**: Visualizaciones estadísticas

### Procesamiento de Archivos
- **openpyxl**: Archivos Excel
- **xlsxwriter**: Escritura Excel
- **pdfplumber**: Lectura de PDFs
- **ReportLab**: Generación de PDFs

### Otros
- **QRCode**: Generación de códigos QR
- **Pillow**: Procesamiento de imágenes
- **python-dotenv**: Variables de entorno

## 💻 Desarrollo

### Estructura de Código

Cada módulo sigue una estructura consistente:

```python
"""
Descripción del módulo
"""

import streamlit as st
from utils.styles import load_custom_css

st.set_page_config(layout="wide", page_title="...", page_icon="...")
load_custom_css()

def main():
    # Encabezado
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>...</h1>
        <div class='header-subtitle'>...</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenido del módulo
    ...

if __name__ == "__main__":
    main()
```

### Convenciones de Código

- **PEP 8**: Seguir las convenciones de estilo de Python
- **Docstrings**: Documentar todas las funciones
- **Type Hints**: Usar anotaciones de tipo cuando sea posible
- **Modularidad**: Mantener funciones pequeñas y reutilizables

### Testing

```bash
# Ejecutar tests (cuando estén disponibles)
pytest tests/
```

## 📝 Notas de la Versión

### v4.0 (2024-02-06)
- ✨ Reestructuración completa del proyecto en módulos
- 🎨 Nuevo diseño de interfaz con CSS personalizado
- 📊 Dashboard de KPIs mejorado
- 💰 Sistema de reconciliación V8 actualizado
- 📧 Módulo de Email AI integrado
- 🚚 Generador de guías con QR
- 📦 Dashboard de transferencias optimizado
- 👥 Gestión de personal mejorada

## 📄 Licencia

Este proyecto es propiedad de AEROPOSTALE Ecuador. Todos los derechos reservados.

## 👨‍💼 Autor

**Wilson Pérez**  
Jefe de Logística & Sistemas  
AEROPOSTALE Ecuador

📧 Email: wperez@fashionclub.com.ec  
🔗 GitHub: [@wilo3161](https://github.com/wilo3161)

---

**© 2024 AEROPOSTALE Ecuador** - Sistema ERP v4.0

Desarrollado con ❤️ por el equipo de Logística y Sistemas
