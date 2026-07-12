import functools
import logging
from datetime import datetime
from database.manager import local_db

logger = logging.getLogger(__name__)

def log_audit(action: str):
    """
    Decorador para registrar acciones de auditoría en la colección AuditLog.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener usuario de los argumentos o de un contexto global (simulado aquí)
            # En una arquitectura real, se pasa el contexto o se obtiene de thread-local storage.
            # Aquí asumimos que el usuario puede ser pasado en kwargs o usamos 'SISTEMA'
            user = kwargs.get('usuario_responsable', 'SISTEMA')
            
            try:
                result = func(*args, **kwargs)
                status = "SUCCESS"
            except Exception as e:
                status = f"FAILED: {str(e)}"
                logger.error(f"Audit action failed: {action}, user: {user}, error: {e}")
                raise
            finally:
                audit_record = {
                    "timestamp": datetime.now().isoformat(),
                    "user": user,
                    "action": action,
                    "status": status,
                    "details": {
                        "args": str(args),
                        "kwargs": {k: str(v) for k, v in kwargs.items()}
                    }
                }
                
                try:
                    if local_db.connected:
                        local_db.db["AuditLog"].insert_one(audit_record)
                except Exception as db_e:
                    logger.error(f"Failed to write audit log: {db_e}")
                    
            return result
        return wrapper
    return decorator
