import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    
    # Avoid duplicate handlers if already setup
    if logger.handlers:
        return
        
    logger.setLevel(logging.INFO)
    
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
