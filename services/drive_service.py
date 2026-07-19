import streamlit as st
import io
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Intentar importar googleapiclient
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
    from google.oauth2 import service_account
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

def _obtener_servicio_drive():
    """Retorna la instancia del servicio Google Drive o lanza excepción si no está disponible."""
    if not GOOGLE_DRIVE_AVAILABLE:
        raise ImportError("google-api-python-client no está instalado")
    
    if "gdrive_service_account" not in st.secrets:
        raise ValueError("Credenciales gdrive_service_account no encontradas en st.secrets")
        
    creds_json = st.secrets["gdrive_service_account"]
    creds_info = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_info, 
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)

def listar_archivos_excel_recientes(service, folder_id=None, limit=10, query_extra=""):
    """
    Busca los archivos Excel recientes (.xlsx, .xls).
    Si folder_id es provisto, busca solo dentro de esa carpeta.
    Retorna lista de diccionarios con id y name.
    """
    try:
        # mimeTypes para excel
        mime_query = "(mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel')"
        q = f"{mime_query} and trashed=false"
        if folder_id:
            q += f" and '{folder_id}' in parents"
        if query_extra:
            q += f" and ({query_extra})"
            
        results = service.files().list(
            q=q,
            spaces='drive',
            fields='files(id, name, createdTime)',
            orderBy='createdTime desc',
            pageSize=limit
        ).execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f"Error listando archivos de Drive: {e}")
        return []

def descargar_archivo_drive(service, file_id):
    """
    Descarga un archivo desde Drive y lo retorna como io.BytesIO.
    """
    try:
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        file_io.seek(0)
        return file_io
    except Exception as e:
        logger.error(f"Error descargando archivo {file_id}: {e}")
        raise e
