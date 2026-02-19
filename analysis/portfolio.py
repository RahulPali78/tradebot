"""Portfolio management."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger('tradebot')


class Portfolio:
    """Track portfolio positions and P&L."""
    
    def __init__(self, trade_history=None):
        """Initialize portfolio.
        
        Args:
            trade_history: TradeHistory database instance
        """
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trade_history = trade_history
    
    def add_position(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        signal: str
    ) -> None:
        """Add a position.
        
        Args:
            symbol: Trading symbol
            quantity: Number of shares
            entry_price: Entry price
            signal: BUY or SELL
        """
        if symbol in self.positions:
            # Average into existing position
            pos = self.positions[symbol]
            total_qty = pos['quantity'] + quantity
            avg_price = (
                (pos['avg_price'] * pos['quantity']) + (entry_price * quantity)
            ) / total_qty
            pos['quantity'] = total_qty
            pos['avg_price'] = avg_price
        else:
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'avg_price': entry_price,
                'entry_time': datetime.now().isoformat(),
                'signal': signal
            }
        
        logger.info(f"Added position: {symbol} {quantity} @ {entry_price}")
    
    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """Close a position.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            
        Returns:
            P&L realized or None
        """
        if symbol not in self.positions:
            logger.warning(f"Position not found: {symbol}")
            return None
        
        pos = self.positions[symbol]
        
        if pos['signal'] == 'BUY':
            pnl = (exit_price - pos['avg_price']) * pos['quantity']
        else:
            pnl = (pos['avg_price'] - exit_price) * pos['quantity']
        
        del self.positions[symbol]
        
        logger.info(f"Closed position: {symbol}, P&L = {pnl:.2f}")
        return pnl
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position dict or None
        """
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_total_exposure(self) -> float:
        """Get total portfolio exposure.
        
        Returns:
            Total exposure amount
        """
        total = 0.0
        for pos in self.positions.values():
            total += pos['quantity'] * pos['avg_price']
        return total
    
    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate unrealized P&L.
        
        Args:
            current_prices: Dictionary of current prices by symbol
            
        Returns:
            Dictionary of P&L by symbol
        """
        pnl = {}
        
        for symbol, pos in self.positions.items():
            if symbol not in current_prices:
                continue
            
            current = current_prices[symbol]
            
            if pos['signal'] == 'BUY':
                pnl[symbol] = (current - pos['avg_price']) * pos['quantity']
            else:
                pnl[symbol] = (pos['avg_price'] - current) * pos['quantity']
        
        return pnl
    
    def clear(self) -> None:
        """Clear all positions."""
        self.positions.clear()
        logger.info("Portfolio cleared")
