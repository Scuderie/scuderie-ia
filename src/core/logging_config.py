"""
Logging Configuration
Structured logging for the application
"""
import logging
import sys
from typing import Optional

# Create logger
_logger: Optional[logging.Logger] = None


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configura il logging strutturato per l'applicazione.
    
    Returns:
        Logger configurato con formato standard
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Create logger
    _logger = logging.getLogger("scuderie")
    _logger.setLevel(level)
    _logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    _logger.propagate = False
    
    return _logger


# Default logger instance
logger = setup_logging()
