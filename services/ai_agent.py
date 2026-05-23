"""
AGENTE IA DUAL — DeepSeek + Gemini
====================================
- DeepSeek como IA principal (agente de monitoreo, detección y corrección)
- Gemini como fallback para transcripción de audio
- Monitorea errores de la app en tiempo real
- Se comunica con el sistema via event_bus
- Capacidad de auto-corrección: detecta error → analiza → propone fix → lo aplica
"""

import streamlit as st
import json
import logging
import sys
import traceback
import re
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuración DeepSeek
DEEPSEEK_API_KEY = "sk-30b…45b7"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

class DeepSeekAgent:
    """
    Agente de IA que monitorea la aplicación en tiempo real,
    detecta errores, los analiza y sugiere/propone correcciones.
    Se comunica con el event_bus para coordinar acciones.
    """
    
    def __init__(self):
        self.session = None
        self._init_client()
        self.error_history = []
        self.auto_fix_enabled = False
    
    def _init_client(self):
        """Inicializa cliente HTTP para DeepSeek API."""
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        })
    
    def _call_deepseek(self, messages: list, temperature: float = 0.1) -> str:
        """
        Llama a la API de DeepSeek.
        """
        try:
            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2000
            }
            resp = self.session.post(DEEPSEEK_URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error llamando a DeepSeek: {e}")
            return f"ERROR_LLAMADA_API: {str(e)}"
    
    def detectar_error(self, error_msg: str, trace: str, modulo: str) -> dict:
        """
        Analiza un error de la aplicación y determina tipo, severidad y posible corrección.
        """
        prompt = f"""Eres un ingeniero de sistemas experto en Python, Streamlit y MongoDB.
Analiza este error de la aplicación ERP Aeropostale:

MÓDULO: {modulo}
ERROR: {error_msg}
TRACEBACK: {trace}

Responde SOLO con JSON válido (sin markdown, sin explicación adicional):
{{
    "tipo_error": "import_error|connection_error|value_error|type_error|runtime_error|key_error|attribute_error|other",
    "severidad": "critico|alto|medio|bajo",
    "causa_raiz": "explicación breve de la causa",
    "archivo_probable": "ruta al archivo con el error",
    "linea_probable": número_de_línea,
    "sugerencia": "qué hacer para corregirlo",
    "auto_fix_posible": true/false,
    "codigo_correccion": "código Python de la corrección (si auto_fix_posible)"
}}"""
        
        result = self._call_deepseek([{"role": "user", "content": prompt}])
        
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = json.loads(result)
            
            analysis["timestamp"] = datetime.now().isoformat()
            analysis["error_original"] = error_msg
            self.error_history.append(analysis)
            
            return analysis
        except:
            return {
                "tipo_error": "unknown",
                "severidad": "medio",
                "causa_raiz": f"No se pudo analizar automáticamente: {error_msg[:200]}",
                "sugerencia": "Revisar logs manualmente",
                "auto_fix_posible": False
            }
    
    def auto_corregir(self, analysis: dict) -> bool:
        """
        Intenta corregir automáticamente un error basado en el análisis.
        Solo si auto_fix_posible = True.
        """
        if not self.auto_fix_enabled or not analysis.get("auto_fix_posible"):
            return False
        
        codigo = analysis.get("codigo_correccion", "")
        archivo = analysis.get("archivo_probable", "")
        
        if not codigo or not archivo:
            return False
        
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(codigo)
            
            logger.info(f"Auto-corrección aplicada en {archivo}")
            
            try:
                from core.event_bus import emitir
                emitir("AUTO_FIX_APLICADO", {
                    "archivo": archivo,
                    "error": analysis.get("error_original", ""),
                    "timestamp": datetime.now().isoformat()
                })
            except:
                pass
            
            return True
        except Exception as e:
            logger.error(f"Auto-corrección falló: {e}")
            return False
    
    def sugerir_mejora_codigo(self, archivo: str, contexto: str) -> str:
        """
        DeepSeek analiza un archivo del código fuente y sugiere mejoras.
        """
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                codigo = f.read()
        except:
            return f"No se pudo leer {archivo}"
        
        prompt = f"""Eres un experto en Python y Streamlit. Analiza este código del ERP Aeropostale:

ARCHIVO: {archivo}
CONTEXTO: {contexto}

CÓDIGO:
```python
{codigo[:4000]}
```

Proporciona:
1. 3 problemas potenciales (bugs, rendimiento, seguridad)
2. 3 mejoras concretas (con código de ejemplo)
3. Prioridad de cada mejora (ALTA/MEDIA/BAJA)

Sé específico y práctico. Usa markdown."""
        
        return self._call_deepseek([{"role": "user", "content": prompt}], temperature=0.3)
    
    def generar_reporte_errores(self) -> str:
        """Genera un reporte de los errores detectados recientemente."""
        if not self.error_history:
            return "No se han detectado errores."
        
        prompt = f"""Genera un reporte ejecutivo de errores del ERP Aeropostale:

ERRORES DETECTADOS:
{json.dumps(self.error_history[-20:], indent=2, default=str)}

Proporciona:
1. Resumen (número de errores por tipo/severidad)
2. Tendencias
3. Recomendaciones priorizadas
Usa markdown."""
        
        return self._call_deepseek([{"role": "user", "content": prompt}], temperature=0.2)
