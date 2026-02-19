"""Trade execution module."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from utils.validators import validate_order_params

logger = logging.getLogger('tradebot')


class MockBrokerAPI:
    """Mock broker API for testing."""
    
    def __init__(self):
        self.order_id_counter = 1000
        self.orders = {}
    
    def place_order(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        price: float,
        product: str = "MIS"
    ) -> Dict[str, Any]:
        """Place a mock order."""
        self.order_id_counter += 1
        order_id = f"ORDER{self.order_id_counter}"
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'price': price,
            'product': product,
            'status': 'COMPLETE',
            'timestamp': datetime.now().isoformat()
        }
        
        self.orders[order_id] = order
        return order
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status."""
        return self.orders.get(order_id, {'status': 'NOT_FOUND'})


class TradeExecutor:
    """Execute trades with validation and logging."""
    
    def __init__(self, broker_api=None, trade_history=None):
        """Initialize trade executor.
        
        Args:
            broker_api: Broker API instance (default: MockBrokerAPI)
            trade_history: TradeHistory database instance
        """
        self.broker = broker_api or MockBrokerAPI()
        self.trade_history = trade_history
    
    def execute_trade(
        self,
        symbol: str,
        signal: str,
        quantity: int,
        price: float,
        confidence: float,
        strategy: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """Execute a trade.
        
        Args:
            symbol: Trading symbol
            signal: BUY or SELL
            quantity: Number of shares
            price: Entry price
            confidence: Trade confidence (0-100)
            strategy: Strategy name
            
        Returns:
            Order result dictionary
        """
        try:
            # Validate inputs
            validate_order_params(symbol, quantity, price)
            
            # Normalize signal
            signal = signal.upper()
            if signal not in ['BUY', 'SELL']:
                raise ValueError(f"Signal must be BUY or SELL, got {signal}")
            
            logger.info(f"Executing trade: {signal} {quantity} {symbol} @ {price}")
            
            # Place order
            order = self.broker.place_order(
                symbol=symbol,
                transaction_type=signal,
                quantity=quantity,
                price=price,
                product="MIS"
            )
            
            logger.info(f"Order placed: {order['order_id']}")
            
            # Log to database
            if self.trade_history:
                trade_data = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'signal': signal,
                    'entry_price': price,
                    'quantity': quantity,
                    'confidence': confidence,
                    'strategy': strategy,
                    'status': 'OPEN'
                }
                trade_id = self.trade_history.log_trade(trade_data)
                order['trade_id'] = trade_id
            
            return order
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            raise
    
    def close_position(
        self,
        trade_id: int,
        exit_price: float
    ) -> Dict[str, Any]:
        """Close an open position.
        
        Args:
            trade_id: Trade ID
            exit_price: Exit price
            
        Returns:
            Close result
        """
        if not self.trade_history:
            logger.warning("No trade history configured")
            return {'success': False}
        
        # Get trade info
        trades = self.trade_history.get_trades(status='OPEN')
        trade = next((t for t in trades if t['id'] == trade_id), None)
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return {'success': False}
        
        # Calculate P&L
        if trade['signal'] == 'BUY':
            pnl = (exit_price - trade['entry_price']) * trade['quantity']
        else:
            pnl = (trade['entry_price'] - exit_price) * trade['quantity']
        
        # Close in database
        self.trade_history.close_trade(trade_id, exit_price, pnl)
        
        logger.info(f"Closed trade {trade_id}: P&L = {pnl:.2f}")
        
        return {
            'success': True,
            'pnl': pnl,
            'trade_id': trade_id
        }
