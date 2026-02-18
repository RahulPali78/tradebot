"""Risk Manager Agent.

Monitors position sizing, margin requirements, exposure limits, and enforces risk rules.
Critical for capital preservation in options trading.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from .base_agent import BaseAgent, AgentResponse


class RiskManager(BaseAgent):
    """Enforces risk management rules and position sizing."""
    
    def __init__(self):
        super().__init__(name="RiskManager", trade_type="BOTH")
        self.description = "Position sizing, margin checks, exposure tracking, max loss limits"
        self.daily_pnl = 0
        self.daily_trades = 0
        self.active_positions = {}
    
    def analyze(self, symbol: str,
                option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None,
                sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Check risk conditions and return approval status."""
        
        metadata = {}
        signals = []
        confidence = 100.0
        config = self._get_risk_config()
        
        # Daily Loss Limit Check
        if self.daily_pnl < -config['max_daily_loss']:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="BLOCK",
                reasoning=f"Daily loss limit breached: ₹{abs(self.daily_pnl)}",
                metadata={'daily_pnl': self.daily_pnl},
                timestamp=datetime.now(), trade_type="BOTH"
            )
        
        # Max Daily Trades Check
        if self.daily_trades >= config['max_daily_trades']:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="BLOCK",
                reasoning=f"Max daily trades reached: {self.daily_trades}",
                metadata={'daily_trades': self.daily_trades},
                timestamp=datetime.now(), trade_type="BOTH"
            )
        
        # Position Size Calculation
        suggested_size = self._calculate_position_size(symbol, option_chain, config)
        metadata['suggested_lots'] = suggested_size
        
        if suggested_size == 0:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="BLOCK",
                reasoning="Position size reduced to 0",
                metadata=metadata, timestamp=datetime.now(), trade_type="BOTH"
            )
        
        # Margin Check
        required_margin = self._estimate_margin(symbol, option_chain, suggested_size)
        available_margin = config['total_capital'] * config['intraday_leverage']
        metadata['required_margin'] = required_margin
        metadata['available_margin'] = available_margin
        
        if required_margin > available_margin * 0.8:
            confidence -= 30
            signals.append(("HOLD", "High margin utilization"))
        
        # Cooling Period
        last_trade = self.active_positions.get(symbol, {}).get('last_trade_time')
        if last_trade:
            mins = (datetime.now() - last_trade).total_seconds() / 60
            if mins < config['cooling_period_minutes']:
                confidence -= 25
                signals.append(("HOLD", f"Cooling period: {mins:.0f}m ago"))
        
        # IV Check
        if option_chain:
            iv_pct = option_chain.get('iv_percentile', 50)
            if iv_pct > 80:
                confidence -= 10
                signals.append(("HOLD", f"High IV {iv_pct}%"))
        
        final_signal = "APPROVE" if confidence >= 70 else "REDUCE" if confidence >= 50 else "BLOCK"
        reasoning = " | ".join([s[1] for s in signals]) if signals else "Risk checks passed"
        
        return AgentResponse(
            agent_name=self.name, confidence=confidence, signal=final_signal,
            reasoning=reasoning, metadata=metadata, timestamp=datetime.now(), trade_type="BOTH"
        )
    
    def _get_risk_config(self) -> Dict:
        return {
            'total_capital': 100000,
            'max_loss_per_trade': 2000,
            'max_daily_loss': 10000,
            'max_daily_trades': 10,
            'intraday_leverage': 4,
            'swing_leverage': 2,
            'cooling_period_minutes': 15,
        }
    
    def _calculate_position_size(self, symbol: str, option_chain: Optional[Dict], config: Dict) -> int:
        if option_chain is None:
            return 1
        premium = option_chain.get('premium', 100)
        lot_size = option_chain.get('lot_size', 50)
        max_lots = config['max_loss_per_trade'] // (premium * lot_size)
        return max(1, min(max_lots, 10))
    
    def _estimate_margin(self, symbol: str, option_chain: Optional[Dict], lots: int) -> float:
        if option_chain is None:
            return lots * 50000
        premium = option_chain.get('premium', 100)
        return lots * premium * option_chain.get('lot_size', 50) * 1.2
    
    def update_position(self, symbol: str, trade_type: str, lots: int, entry_price: float):
        self.daily_trades += 1
        self.active_positions[symbol] = {
            'trade_type': trade_type, 'lots': lots,
            'entry_price': entry_price, 'last_trade_time': datetime.now()
        }
    
    def close_position(self, symbol: str, exit_price: float):
        if symbol in self.active_positions:
            pos = self.active_positions[symbol]
            pnl = (exit_price - pos['entry_price']) * pos['lots'] * 50
            self.daily_pnl += pnl
            del self.active_positions[symbol]
    
    def reset_daily_stats(self):
        self.daily_pnl = 0
        self.daily_trades = 0
