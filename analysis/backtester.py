"""Backtesting framework for tradebot."""
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('tradebot')


class Backtester:
    """Backtest trading strategies."""
    
    def __init__(
        self,
        strategy: Callable,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0
    ):
        """Initialize backtester."""
        self.strategy = strategy
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.initial_capital = initial_capital
    
    def run(
        self,
        symbol: str,
        data_fetcher: Callable
    ) -> Dict[str, Any]:
        """Run backtest."""
        results = []
        capital = self.initial_capital
        trades = []
        position = None
        
        logger.info(f"Starting backtest for {symbol}")
        
        current = self.start_date
        while current <= self.end_date:
            try:
                data = data_fetcher(symbol, current)
                if not data:
                    current += timedelta(days=1)
                    continue
                
                # Get decision from strategy
                decision = self.strategy.analyze(symbol)
                
                if decision and decision.get('confidence', 0) >= 70:
                    results.append(decision)
                    
                    # Simulate trade
                    if not position:
                        position = {
                            'symbol': symbol,
                            'signal': decision['signal'],
                            'entry_price': decision.get('ltp', 0),
                            'entry_date': current
                        }
                    elif position['signal'] != decision['signal']:
                        # Close position
                        exit_price = decision.get('ltp', 0)
                        pnl = (exit_price - position['entry_price']) * 100
                        trades.append({
                            'signal': position['signal'],
                            'entry': position['entry_price'],
                            'exit': exit_price,
                            'pnl': pnl
                        })
                        position = None
                
                current += timedelta(days=1)
                
            except Exception as e:
                logger.error(f"Backtest error on {current}: {e}")
                current += timedelta(days=1)
        
        return self.calculate_metrics(results, trades)
    
    def calculate_metrics(
        self,
        results: List[Dict[str, Any]],
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate backtest metrics."""
        total_trades = len(trades)
        if total_trades == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0
            }
        
        wins = len([t for t in trades if t.get('pnl', 0) > 0])
        losses = len([t for t in trades if t.get('pnl', 0) < 0])
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total_trades,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / total_trades
        }
