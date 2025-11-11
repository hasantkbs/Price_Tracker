import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create handlers
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    
    stdout_handler.setLevel(logging.DEBUG)
    stderr_handler.setLevel(logging.ERROR)
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(log_format)
    stderr_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    
    return logger
