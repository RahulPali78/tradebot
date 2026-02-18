"""Base agent class for the NSE Options Trading System.

All specialist agents inherit from this base class to ensure consistent interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class AgentResponse:
    """Standardized response from any agent in the system."""
    
    agent_name: str
    confidence: float  # 0-100 score
    signal: str  # 'BUY', 'SELL', 'HOLD', or 'NO_SIGNAL'
    reasoning: str  # Detailed explanation
    metadata: Dict[str, Any]  # Additional data (Greeks, levels, etc.)
    timestamp: datetime
    trade_type: str  # 'INTRADAY' or 'SWING'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return {
            'agent_name': self.agent_name,
            'confidence': self.confidence,
            'signal': self.signal,
            'reasoning': self.reasoning,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'trade_type': self.trade_type,
        }


class BaseAgent(ABC):
    """Abstract base class for all trading agents."""
    
    def __init__(self, name: str, trade_type: str = "INTRADAY"):
        """Initialize the agent.
        
        Args:
            name: Unique identifier for this agent
            trade_type: 'INTRADAY' or 'SWING'
        """
        self.name = name
        self.trade_type = trade_type
        self.enabled = True
        self.reliability_score = 0.5  # Tracked over time (0-1)
    
    @abstractmethod
    def analyze(self, symbol: str, 
                option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None,
                sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze market conditions and return a trading signal.
        
        Args:
            symbol: Stock symbol (e.g., 'NIFTY', 'RELIANCE')
            option_chain: Raw option chain data
            market_data: Price/volume data
            sentiment_data: News/FII flow data
            
        Returns:
            AgentResponse with confidence score and reasoning
        """
        pass
    
    def validate_inputs(self, **kwargs) -> bool:
        """Validate that required inputs are present."""
        return True
    
    def update_reliability(self, trade_result: float):
        """Update reliability score based on trade outcome.
        
        Args:
            trade_result: P&L from the trade (positive for profit)
        """
        # Exponential moving average of trade success
        success = 1 if trade_result > 0 else 0
        self.reliability_score = 0.9 * self.reliability_score + 0.1 * success
