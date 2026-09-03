import logging

def setup_logging():
    logger = logging.getLogger()
    
    # Avoid duplicate handlers if already setup
    if logger.handlers:
        return
        
    logger.setLevel(logging.INFO)
    
    logHandler = logging.StreamHandler()
    try:
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    except ImportError:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
