# MODIFIED: 2026-05-21 - Added exportar_reporte unified export function
from utils.ui import add_back_button
from utils.common import hash_password, normalizar_texto, procesar_subtotal, identificar_tipo_tienda

import streamlit as st
import pandas as pd
import io

def exportar_reporte(df, nombre_base="reporte", formato="excel"):
    """
    Exporta un DataFrame a Excel, CSV o PDF y devuelve bytes + mime + filename.
    Uso: st.download_button(*exportar_reporte(df, "inventario"))
    """
    if df is None or df.empty:
        return None, None, None
    
    if formato == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=nombre_base[:31])
            ws = writer.sheets[nombre_base[:31]]
            for col_idx, col in enumerate(df.columns, 1):
                max_len = max(len(str(col)), df[col].astype(str).str.len().max()) if len(df) > 0 else len(str(col))
                ws.column_dimensions[chr(64 + col_idx)].width = min(max_len + 2, 50)
        output.seek(0)
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"{nombre_base}.xlsx"
    
    elif formato == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        return output.getvalue().encode('utf-8-sig'), "text/csv", f"{nombre_base}.csv"
    
    elif formato == "pdf":
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"Reporte: {nombre_base}", styles['Title']))
            
            data = [df.columns.tolist()] + df.astype(str).values.tolist()
            t = Table(data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0,0.18,0.38)),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.Color(0.95,0.95,0.95)]),
            ]))
            elements.append(t)
            doc.build(elements)
            output.seek(0)
            return output.getvalue(), "application/pdf", f"{nombre_base}.pdf"
        except ImportError:
            st.warning("ReportLab no instalado. Usando CSV como fallback.")
            return exportar_reporte(df, nombre_base, "csv")
    
    return None, None, None
