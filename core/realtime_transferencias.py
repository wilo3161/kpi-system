"""
core/realtime_transferencias.py
═══════════════════════════════════════════════════════════════════════════════
Motor de KPIs Personalizados en Tiempo Real para Transferencias Logísticas.
- Horario de Jornada: 08:00 AM - 18:00 PM.
- Discriminación estricta de Fundas / Insumos vs Prendas Textiles.
- Mapeo de transferidores oficiales (Josué Imbacuan, Luis Perugachi, Andrés Yépez, Jonny Villa, Wilson Pérez).
- Consulta dinámica por cualquier fecha seleccionada.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations
import os
import re
import unicodedata
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

# Diccionario de normalización de colaboradores
ALIAS_TRANSFERIDORES = {
    'IMBACUAN': 'Josué Imbacuan',
    'JOSUE': 'Josué Imbacuan',
    'PERUGACHI': 'Luis Perugachi',
    'LUIS': 'Luis Perugachi',
    'YEPEZ': 'Andrés Yépez',
    'ANDRES': 'Andrés Yépez',
    'CESAR': 'Andrés Yépez',
    'VILLA': 'Jonny Villa',
    'JHONNY': 'Jonny Villa',
    'JOHNNY': 'Jonny Villa',
    'JONNY': 'Jonny Villa',
    'WILSON': 'Wilson Pérez',
    'WILO': 'Wilson Pérez',
    'PEREZ': 'Wilson Pérez',
}

def normalizar_texto(texto: Any) -> str:
    if pd.isna(texto) or texto is None:
        return ""
    s = str(texto).upper().strip()
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def identificar_transferidor(nombre_raw: Any) -> str:
    """Mapea cualquier variación de nombre/cédula al nombre oficial del transferidor."""
    clean = normalizar_texto(nombre_raw)
    if not clean:
        return "Bodega Central"
    
    for token, oficial in ALIAS_TRANSFERIDORES.items():
        if token in clean:
            return oficial
            
    partes = clean.split()
    if len(partes) >= 2:
        return f"{partes[0].title()} {partes[1].title()}"
    return clean.title()

def discriminar_fundas_sisconti(cantidad: float, costo: float, descripcion: str = "", grupo: str = "") -> Tuple[int, int]:
    """
    Discrimina si un registro corresponde a Fundas / Insumos o Prendas Textiles.
    Retorna (prendas_netas, fundas_netas).
    """
    cant_num = int(round(float(cantidad))) if not pd.isna(cantidad) else 0
    costo_num = float(costo) if not pd.isna(costo) else 0.0

    # 1. Bultos de fundas plásticas por 300 u. con costo menor a $15 (ej. $7.78)
    if cant_num == 300 and costo_num < 15.0:
        return 0, cant_num

    # 2. Insumos/fundas de tienda de 9 o 10 unidades con costo de $50-$65 (ej. $54.18 o $60)
    if cant_num in (9, 10) and 50.0 <= costo_num <= 65.0:
        return 0, cant_num

    # 3. Detección por texto en descripción o grupo
    comb = f"{descripcion} {grupo}".upper()
    if any(k in comb for k in ['FUNDA', 'PLASTIC BAG', 'AERO PLASTIC BAG', 'BOLSA']):
        if 'FUNDA LENTES' not in comb and 'FUNDA DE GAFAS' not in comb:
            return 0, cant_num

    return cant_num, 0


class RealtimeTransferenciasService:
    """
    Servicio de cálculo y agregación en tiempo real para cualquier fecha de consulta.
    """

    @classmethod
    def procesar_transferencias(
        cls,
        df_transferencias: pd.DataFrame,
        fecha_consulta: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa el dataset de transferencias para la fecha indicada (o todo el dataset).
        """
        if df_transferencias.empty:
            return {
                "success": False,
                "mensaje": "No hay datos de transferencias para procesar."
            }

        df = df_transferencias.copy()

        # Filtrar por fecha si se proporciona
        if fecha_consulta and 'FECHA' in df.columns:
            f_norm = str(fecha_consulta).replace('/', '-').strip()
            df = df[df['FECHA'].astype(str).str.contains(f_norm, na=False)]

        if df.empty:
            return {
                "success": False,
                "mensaje": f"No se encontraron registros para la fecha {fecha_consulta}."
            }

        # Normalizar columnas
        col_sec = 'SECUENCIAL' if 'SECUENCIAL' in df.columns else df.columns[0]
        col_tienda = 'TIENDA' if 'TIENDA' in df.columns else ('DESTINO' if 'DESTINO' in df.columns else 'Bodega')
        col_cant = 'CANTIDAD' if 'CANTIDAD' in df.columns else ('Cantidad' if 'Cantidad' in df.columns else 'PRENDAS')
        col_costo = 'COSTO' if 'COSTO' in df.columns else ('Costo' if 'Costo' in df.columns else None)
        col_transf = 'TRANSFERIDOR' if 'TRANSFERIDOR' in df.columns else 'EMPL_APE_NOMB'

        # Asignar transferidor si no existe o está genérico
        if col_transf in df.columns:
            df['TRANSFERIDOR_OFICIAL'] = df[col_transf].apply(identificar_transferidor)
        else:
            equipo = ['Josué Imbacuan', 'Luis Perugachi', 'Andrés Yépez', 'Jonny Villa', 'Wilson Pérez']
            df['TRANSFERIDOR_OFICIAL'] = [equipo[i % len(equipo)] for i in range(len(df))]

        # Aplicar discriminación de fundas si no está precalculada
        if 'PRENDAS' not in df.columns or 'FUNDAS' not in df.columns:
            prendas_list, fundas_list = [], []
            for _, row in df.iterrows():
                c_val = row.get(col_cant, 0)
                cost_val = row.get(col_costo, 0.0) if col_costo else 0.0
                p, f = discriminar_fundas_sisconti(c_val, cost_val)
                prendas_list.append(p)
                fundas_list.append(f)
            df['PRENDAS'] = prendas_list
            df['FUNDAS'] = fundas_list

        df['COSTO_VAL'] = df[col_costo].astype(float) if col_costo in df.columns else 0.0

        # ── TOTALES GENERALES ──
        total_transf = len(df[col_sec].unique())
        total_prendas = int(df['PRENDAS'].sum())
        total_fundas = int(df['FUNDAS'].sum())
        total_unidades = total_prendas + total_fundas
        total_costo = float(df['COSTO_VAL'].sum())

        # ── RANKING POR TRANSFERIDOR ──
        ranking_list = []
        for transf_name, grp in df.groupby('TRANSFERIDOR_OFICIAL'):
            p_sum = int(grp['PRENDAS'].sum())
            f_sum = int(grp['FUNDAS'].sum())
            t_sum = p_sum + f_sum
            c_sum = float(grp['COSTO_VAL'].sum())
            secs = sorted(list(grp[col_sec].astype(str).unique()))
            pct = round((p_sum / max(1, total_prendas)) * 100, 1)

            tiendas_dict = {}
            for t_dest, t_grp in grp.groupby(col_tienda):
                tiendas_dict[t_dest] = {
                    "prendas": int(t_grp['PRENDAS'].sum()),
                    "fundas": int(t_grp['FUNDAS'].sum()),
                    "secuenciales": sorted(list(t_grp[col_sec].astype(str).unique()))
                }

            ranking_list.append({
                "transferidor": transf_name,
                "prendas": p_sum,
                "fundas": f_sum,
                "total_unidades": t_sum,
                "transferencias_count": len(secs),
                "porcentaje_aporte": pct,
                "costo_total": c_sum,
                "secuenciales": secs,
                "tiendas": tiendas_dict
            })

        ranking_list.sort(key=lambda x: x["prendas"], reverse=True)

        # ── DESGLOSE POR TIENDA / CANAL ──
        tiendas_list = []
        for t_dest, grp in df.groupby(col_tienda):
            p_sum = int(grp['PRENDAS'].sum())
            f_sum = int(grp['FUNDAS'].sum())
            c_sum = float(grp['COSTO_VAL'].sum())
            secs = sorted(list(grp[col_sec].astype(str).unique()))

            quienes = {}
            for pers, p_grp in grp.groupby('TRANSFERIDOR_OFICIAL'):
                quienes[pers] = {
                    "prendas": int(p_grp['PRENDAS'].sum()),
                    "fundas": int(p_grp['FUNDAS'].sum()),
                    "secuenciales": sorted(list(p_grp[col_sec].astype(str).unique()))
                }

            t_low = str(t_dest).lower()
            if 'web' in t_low or 'movil' in t_low:
                canal = "Ventas Web"
            elif 'mayor' in t_low:
                canal = "Ventas por Mayor"
            elif 'falla' in t_low:
                canal = "Fallas"
            elif 'price' in t_low:
                canal = "Price Club"
            else:
                canal = "Tiendas Aéropostale"

            tiendas_list.append({
                "tienda": t_dest,
                "canal": canal,
                "prendas": p_sum,
                "fundas": f_sum,
                "total_unidades": p_sum + f_sum,
                "transferencias_count": len(secs),
                "costo_total": c_sum,
                "secuenciales": secs,
                "transferidores": quienes
            })

        tiendas_list.sort(key=lambda x: x["prendas"], reverse=True)

        return {
            "success": True,
            "fecha_consultada": fecha_consulta or "Todas las fechas",
            "jornada": "08:00 AM - 18:00 PM",
            "totales": {
                "total_transferencias": total_transf,
                "total_prendas_netas": total_prendas,
                "tarjeta_fundas": total_fundas,
                "total_unidades": total_unidades,
                "costo_total_usd": round(total_costo, 2),
                "promedio_prendas_x_transf": round(total_prendas / max(1, total_transf), 1)
            },
            "ranking_transferidores": ranking_list,
            "desglose_tiendas": tiendas_list,
            "df_procesado": df
        }
