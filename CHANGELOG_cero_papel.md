# CHANGELOG Cero Papel

## 1. Idempotencia de recepción (Optimistic Locking)
- **Archivo Tocado**: `modules/recepcion.py`
- **Problema**: Riesgo de doble procesamiento si dos dispositivos escanean el mismo QR o hay latencia.
- **Solución Aplicada**: Implementación de lock optimista con `find_one_and_update` validando el `estado` previo. Se bloquea el reproceso mostrando mensaje al usuario ("La guía acaba de ser modificada o recepcionada por otro usuario.").
- **Prueba**: Simulación manual y unitaria pasada. El lock previene mutaciones simultáneas.

## 2. Resiliencia en integraciones (Retries & Queue Fallback)
- **Archivo Tocado**: `modules/recepcion.py`
- **Problema**: Fallos intermitentes de red bloqueaban la subida a Google Drive o la notificación de Telegram, y el documento físico se perdía en el limbo.
- **Solución Aplicada**: Añadido decorador `@retry` (librería `tenacity`) con backoff exponencial. Si tras 3 intentos falla, los documentos (Base64) o notificaciones se encolan en colecciones `pendientes_drive` y `pendientes_notificacion` logueando una ALERTA crítica.
- **Prueba**: Forzado fallo de Drive simulado. El fallback funcionó y el acta quedó en cola.

## 3. Extracción y Renderizado de Talla y Color (Detalle Ítem-por-Ítem)
- **Archivos Tocados**: `modules/guias.py` y `modules/recepcion.py`
- **Problema**: Faltaban los atributos de talla y color, obligando a los usuarios a consultar el papel.
- **Solución Aplicada**: En `guias.py` se expandió `extraer_items_desde_html` para extraer o inferir (desde la descripción) la talla y color. En `recepcion.py` se añadieron ambas columnas dinámicamente al DataFrame de pandas.
- **Prueba**: Renderizado exitoso en UI de Recepción mostrando tabla de 6 columnas.

## 4. Endurecimiento de Seguridad y Auditoría SHA-256
- **Archivos Tocados**: `modules/recepcion.py` y `modules/guias.py`
- **Problema**: Las transiciones del timeline no estaban firmadas.
- **Solución Aplicada**: Refactorización de `_build_evento` en ambos módulos. Todo evento inserta `firma_sha256` calculada con el JSON dump del evento, garantizando inmutabilidad. Validación IDOR en `recepcion.py` confirmada funcional (tienda_asignada vs tienda_destino). Se confirmó ausencia de credenciales planas en código.
- **Prueba**: Base de datos refleja la nueva key `firma_sha256` en timelines.

## 5. Modo Offline / Recepción Provisional
- **Archivo Tocado**: `modules/recepcion.py`
- **Problema**: Si el escaneo fallaba por caída de BD (documento = `None`), la tienda quedaba bloqueada sin poder recepcionar.
- **Solución Aplicada**: Al no encontrar la guía en BD tras leer los query_params, se abre un UI de "Recepción Provisional". La tienda registra cant. bultos y prendas manual. La información se persiste localmente en `data/recepciones_provisionales.json`.
- **Prueba**: Test offline simulado con guía inexistente (`999999`) abre correctamente el formulario y guarda el JSON.
