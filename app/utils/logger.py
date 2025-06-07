import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# Create logs directory if it doesn't exist
logs_dir = os.environ.get('LOGS_DIR', '/logs')
if not os.path.exists(logs_dir):
    try:
        os.makedirs(logs_dir)
    except Exception as e:
        print(f"Error creating logs directory: {e}")
        logs_dir = '/tmp'  # Fallback to /tmp if logs directory can't be created

# Configure logging format
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_logger(name):
    """
    Create and configure a logger with both console and file handlers.
    
    The logger will:
    - Output to stdout with a formatted message
    - Write to a rotating log file (10MB max, 5 backups)
    - Respect the LOG_LEVEL environment variable
    
    Args:
        name (str): Logger name (typically __name__ when called from a module)
        
    Returns:
        logging.Logger: Configured logger instance with both console and file handlers.
        
    Notes:
        - Log files are stored in the directory specified by LOGS_DIR environment variable
          (defaults to '/logs') or '/tmp' if the specified directory cannot be created
        - Log level can be set via LOG_LEVEL environment variable (defaults to INFO)
        - Prevents duplicate handlers if called multiple times with the same name
    """
    logger = logging.getLogger(name)
    
    # Set log level from environment variable or default to INFO
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Add console handler if not already present
    if not any(
        isinstance(h, logging.StreamHandler) and h.stream == sys.stdout 
        for h in logger.handlers
    ):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)
    
    # Configure and add file handler if not already present
    log_file = os.path.join(logs_dir, f"{name.split('.')[-1]}.log")
    if not any(
        isinstance(h, RotatingFileHandler) and h.baseFilename == log_file 
        for h in logger.handlers
    ):
        try:
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to create log file handler: {e}")
    
    return logger
