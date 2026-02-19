"""Input validation utilities."""
import re
from typing import Tuple, List, Dict, Any

VALID_SYMBOLS = {
    'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX',
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
}


def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol.
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If symbol is invalid
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a string")
    
    if len(symbol) > 20:
        raise ValueError(f"Symbol too long: {symbol}")
    
    if not symbol.isupper():
        raise ValueError("Symbol must be uppercase")
    
    if not re.match(r'^[A-Z]+$', symbol):
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    return True


def validate_order_params(symbol: str, quantity: int, price: float) -> bool:
    """Validate order parameters.
    
    Args:
        symbol: Trading symbol
        quantity: Order quantity
        price: Order price
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If parameters are invalid
    """
    validate_symbol(symbol)
    
    if not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"Quantity must be a positive integer, got {quantity}")
    
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError(f"Price must be a positive number, got {price}")
    
    return True


def validate_threshold(threshold: float) -> bool:
    """Validate confidence threshold.
    
    Args:
        threshold: Threshold value (0-100)
        
    Returns:
        True if valid
    """
    if not isinstance(threshold, (int, float)):
        raise ValueError("Threshold must be a number")
    
    if not 0 <= threshold <= 100:
        raise ValueError(f"Threshold must be between 0 and 100, got {threshold}")
    
    return True


def validate_date_range(start_date: str, end_date: str) -> Tuple[str, str]:
    """Validate date range.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Tuple of validated dates
    """
    from datetime import datetime
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end