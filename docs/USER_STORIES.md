# USER_STORIES.md — Historias de Usuario

## Roles del Sistema

| Rol | Descripción |
|-----|-------------|
| **Administrador** | Acceso total. Gestiona usuarios, configuración, uploads de inventario, y administración del sistema. |
| **Logística** | Gestiona transferencias, recepciones, guías, KPIs logísticos y dashboard. |
| **Bodega** | Gestiona guías, inventario, almacén y recepción de mercancía. |
| **Ventas** | Consulta KPIs, dashboards y reportes (solo lectura). |

## Historias por Rol

### Administrador
- ADM-01: Como administrador, quiero cargar archivos de inventario para que los usuarios puedan consultar stock.
- ADM-02: Como administrador, quiero gestionar usuarios y roles para controlar accesos.
- ADM-03: Como administrador, quiero ver logs de auditoría para rastrear cambios.
- ADM-04: Como administrador, quiero configurar parámetros del sistema (metas, umbrales, colores).
- ADM-05: Como administrador, quiero entrenar modelos de predicción para anticipar demanda.
- ADM-06: Como administrador, quiero crear índices en MongoDB para optimizar consultas.

### Logística
- LOG-01: Como logistico, quiero cargar transferencias diarias para registrar la distribución.
- LOG-02: Como logistico, quiero ver KPIs de exactitud de despacho y OTIF.
- LOG-03: Como logistico, quiero generar guías de envío con seguimiento QR.
- LOG-04: Como logistico, quiero ver pronósticos de demanda para planificar stock.
- LOG-05: Como logistico, quiero conciliar facturas y transferencias.
- LOG-06: Como logistico, quiero ver el análisis ABC de productos para priorizar gestión.
- LOG-07: Como logistico, quiero recibir alertas de stock bajo y guías con recepción pendiente.

### Bodega
- BOD-01: Como bodeguero, quiero registrar recepción de guías con diferencias.
- BOD-02: Como bodeguero, quiero consultar el inventario por código o descripción.
- BOD-03: Como bodeguero, quiero generar guías de envío para preparar pedidos.
- BOD-04: Como bodeguero, quiero ver el layout de bodega para ubicar productos.
- BOD-05: Como bodeguero, quiero asignar ubicaciones físicas a productos.
- BOD-06: Como bodeguero, quiero generar picking lists optimizados por ruta.
- BOD-07: Como bodeguero, quiero programar y registrar conteos cíclicos de inventario.

### Ventas
- VEN-01: Como vendedor, quiero ver el dashboard de KPIs globales.
- VEN-02: Como vendedor, quiero consultar disponibilidad de inventario.
- VEN-03: Como vendedor, quiero ver análisis ABC de productos.
- VEN-04: Como vendedor, quiero ver predicciones de demanda para planificar pedidos.

## Flujos Principales

1. **Carga de Transferencias** → Cruce de datos → Cálculo de KPIs → Histórico → Forecast
2. **Generación de Guía** → Asignación de transportista → Recepción en tienda → Cierre
3. **Carga de Inventario (Admin)** → Validación de columnas → Generación de SKU → Almacenamiento
4. **Dashboard KPIs** → Consulta a BD → Cálculo de métricas → Visualización → Insights IA
5. **Predicción de Demanda** → Datos históricos → Modelo ML → Pronóstico 7 días
6. **Gestión de Almacén** → Asignación de ubicaciones → Picking → Despacho → Conteo cíclico
7. **Análisis ABC** → Datos de inventario → Clasificación por valor → Priorización de gestión
