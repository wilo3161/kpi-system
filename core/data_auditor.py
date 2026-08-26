"""
core/data_auditor.py
═══════════════════════════════════════════════════════════════════════════════
Motor de Auditoría, Integridad y Data Quality para KPI System.
- Validación de campos requeridos (Bronze -> Silver).
- Generación de hashes únicos para mecanismo de Upsert idempotente.
- Detección y cuarentena de registros corruptos o anómalos.
═══════════════════════════════════════════════════════════════════════════════
"""

import hashlib
import re
from datetime import date, datetime
from typing import Any, Dict, List, Tuple
import pandas as pd


class DataAuditor:
    """Motor de validación de integridad y Data Quality para transferencias."""

    @staticmethod
    def generar_hash_transferencia(secuencial: str, fecha: Any, tienda: str, transferidor: str) -> str:
        """Genera un hash SHA-256 único e idempotente para cada registro de transferencia."""
        f_str = str(fecha).strip() if fecha else "1970-01-01"
        raw = f"{str(secuencial).strip().upper()}_{f_str}_{str(tienda).strip().upper()}_{str(transferidor).strip().upper()}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @classmethod
    def auditar_dataset_transferencias(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Inspecciona el dataset crudo, detecta registros incompletos o anómalos
        y separa los registros limpios de los registros en cuarentena.
        """
        if df is None or df.empty:
            return pd.DataFrame(), []

        errores = []
        registros_validos = []

        for idx, row in df.iterrows():
            sec = str(row.get('SECUENCIAL', row.get('minv_num_sec', ''))).strip()
            cant = row.get('PRENDAS', row.get('CANTIDAD', row.get('Trans_ Can', row.get('CANTIDAD_TRANS', 0))))
            tienda = str(row.get('TIENDA', row.get('Nombre Bode.', row.get('BODEGA_DESTINO', '')))).strip()
            fecha = row.get('FECHA', row.get('Fecha_Trans', None))
            transferidor = str(row.get('TRANSFERIDOR', row.get('empl_ape_nomb', 'Bodega Central'))).strip()

            # Validar campos obligatorios
            if not sec or sec.lower() in ['nan', 'none', '']:
                errores.append({'fila': idx, 'error': 'Secuencial de transferencia vacío o nulo'})
                continue
            if cant is None:
                errores.append({'fila': idx, 'secuencial': sec, 'error': 'Cantidad no especificada'})
                continue
            if not tienda or tienda.lower() in ['nan', 'none', '']:
                errores.append({'fila': idx, 'secuencial': sec, 'error': 'Tienda destino no especificada'})
                continue

            row_dict = dict(row)
            row_dict['SECUENCIAL'] = sec
            row_dict['hash_registro'] = cls.generar_hash_transferencia(sec, fecha, tienda, transferidor)
            registros_validos.append(row_dict)

        df_limpio = pd.DataFrame(registros_validos) if registros_validos else pd.DataFrame()
        return df_limpio, errores
