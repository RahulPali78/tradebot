"""Decorators for tradebot."""
import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger('tradebot')


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """Retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise last_exception
                    
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


def validate_symbol(func: Callable) -> Callable:
    """Decorator to validate symbol parameter.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if symbol is in args (first positional arg after self) or kwargs
        symbol = None
        if len(args) >= 2:
            symbol = args[1]  # First arg after self
        elif 'symbol' in kwargs:
            symbol = kwargs['symbol']
        
        if symbol is not None:
            if not symbol or len(symbol) > 20:
                raise ValueError(f"Invalid symbol: {symbol}")
            if not symbol.isupper():
                raise ValueError("Symbol must be uppercase")
        
        return func(*args, **kwargs)
    return wrapper


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} executed in {elapsed:.2f}s")
        return result
    return wrapper
