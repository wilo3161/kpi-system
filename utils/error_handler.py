"""
Manejador global de errores para el ERP Aeropostale.
Intercepta excepciones no capturadas y las envía al agente DeepSeek.
"""

import streamlit as st
import sys
import traceback

ORIGINAL_EXCEPTHOOK = None

def setup_global_error_handler():
    """
    Configura un hook global que captura TODAS las excepciones no manejadas
    y las envía al agente DeepSeek para análisis.
    """
    global ORIGINAL_EXCEPTHOOK
    
    def deepseek_excepthook(exc_type, exc_value, exc_tb):
        """Hook personalizado que captura excepciones y las analiza con IA."""
        try:
            from modules.monitor_errores import capturar_y_analizar
            modulo = "sistema"
            if exc_tb:
                frame = exc_tb.tb_frame
                while frame:
                    filename = frame.f_code.co_filename
                    if 'modules' in filename:
                        modulo = filename.split('modules')[-1].replace('\\', '/').strip('/')
                        break
                    frame = frame.f_back
            
            capturar_y_analizar(exc_value, modulo)
        except:
            pass
        
        if ORIGINAL_EXCEPTHOOK:
            ORIGINAL_EXCEPTHOOK(exc_type, exc_value, exc_tb)
    
    ORIGINAL_EXCEPTHOOK = sys.excepthook
    sys.excepthook = deepseek_excepthook
