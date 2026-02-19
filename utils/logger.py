"""Logging utilities for tradebot."""
import logging
import os
from datetime import datetime


def setup_logging(
    level: int = logging.INFO,
    log_file: str = None,
    format_str: str = None
) -> logging.Logger:
    """Setup logging with file and stream handlers.
    
    Args:
        level: Logging level
        log_file: Path to log file (default: trading_agent.log)
        format_str: Custom format string
        
    Returns:
        Configured logger
    """
    if log_file is None:
        log_file = f"trading_agent_{datetime.now().strftime('%Y%m%d')}.log"
    
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logger = logging.getLogger('tradebot')
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(file_handler)
    
    # Stream handler (console)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(stream_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (default: tradebot)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'tradebot.{name}')
    return logging.getLogger('tradebot')
