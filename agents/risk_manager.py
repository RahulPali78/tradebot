"""Risk Manager Agent."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.decorators import validate_symbol, log_execution_time
from utils.logger import get_logger
from agents.base_agent import BaseAgent, AgentResponse

logger = get_logger('risk_manager')


class RiskManager(BaseAgent):
    """Enforces risk management rules."""
    
    # Correlation matrix for major indices
    CORRELATION_MATRIX = {
        ('NIFTY', 'MIDCPNIFTY'): 0.9,
        ('NIFTY', 'BANKNIFTY'): 0.8,
        ('NIFTY', 'FINNIFTY'): 0.75,
        ('BANKNIFTY', 'FINNIFTY'): 0.6,
        ('BANKNIFTY', 'MIDCPNIFTY'): 0.7,
        ('FINNIFTY', 'MIDCPNIFTY'): 0.65,
    }
    
    def __init__(self, max_exposure: float = 100000):
        super().__init__(name="RiskManager", trade_type="BOTH")
        self.description = "Position sizing, margin checks, exposure limits"
        self.max_exposure = max_exposure
        self.daily_pnl = 0
        self.daily_trades = 0
        self.active_positions = {}
    
    def check_position_correlation(
        self,
        new_symbol: str,
        existing_positions: List[str]
    ) -> tuple:
        """Check if new position is highly correlated with existing ones.
        
        Returns:
            (is_valid, message)
        """
        for symbol in existing_positions:
            key = tuple(sorted([new_symbol, symbol]))
            corr = self.CORRELATION_MATRIX.get(key, 0)
            if corr > 0.7:
                msg = f"High correlation ({corr}) with {symbol}"
                logger.warning(f"Correlation check failed: {msg}")
                return False, msg
        return True, "No correlation issues"
    
    def analyze(self, symbol: str, option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None, sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Check risk conditions."""
        logger.info(f"Checking risk for {symbol}")
        
        config = self._get_risk_config()
        signals = []
        confidence = 100.0
        
        # Daily loss limit
        if self.daily_pnl < -config['max_daily_loss']:
            logger.warning(f"Daily loss limit breached: {abs(self.daily_pnl)}")
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="BLOCK",
                reasoning=f"Daily loss limit breached", metadata={},
                timestamp=datetime.now(), trade_type="BOTH"
            )
        
        # Max trades
        if self.daily_trades >= config['max_daily_trades']:
            logger.warning(f"Max daily trades reached: {self.daily_trades}")
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="BLOCK",
                reasoning="Max daily trades reached", metadata={},
                timestamp=datetime.now(), trade_type="BOTH"
            )
        
        # Correlation check
        existing = list(self.active_positions.keys())
        valid, msg = self.check_position_correlation(symbol, existing)
        if not valid:
            confidence -= 30
            signals.append(("HOLD", msg))
        
        # Position size
        suggested = self._calculate_position_size(symbol, option_chain, config)
        metadata = {'suggested_lots': suggested}
        
        if suggested == 0:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="BLOCK",
                reasoning="Position size zero", metadata=metadata,
                timestamp=datetime.now(), trade_type="BOTH"
            )
        
        # Confidence thresholds
        final_signal = "APPROVE" if confidence >= 70 else "BLOCK"
        
        logger.info(f"Risk check for {symbol}: {final_signal}")
        
        return AgentResponse(
            agent_name=self.name, confidence=confidence, signal=final_signal,
            reasoning="Risk checks passed", metadata=metadata,
            timestamp=datetime.now(), trade_type="BOTH"
        )
    
    def _get_risk_config(self) -> Dict:
        return {
            'total_capital': self.max_exposure,
            'max_loss_per_trade': self.max_exposure * 0.02,
            'max_daily_loss': self.max_exposure * 0.1,
            'max_daily_trades': 10,
        }
    
    def _calculate_position_size(self, symbol, option_chain, config):
        return 1
    
    def update_position(self, symbol: str, trade_type: str, lots: int, entry_price: float):
        self.daily_trades += 1
        self.active_positions[symbol] = {
            'trade_type': trade_type, 'lots': lots,
            'entry_price': entry_price, 'last_trade_time': datetime.now()
        }
