"""Swing Strategy Agent."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np

from utils.decorators import validate_symbol, log_execution_time
from utils.logger import get_logger
from agents.base_agent import BaseAgent, AgentResponse

logger = get_logger('swing_agent')


class SwingStrategyAgent(BaseAgent):
    """Generates swing trading signals based on positional analysis."""
    
    def __init__(self):
        super().__init__(name="SwingStrategyAgent", trade_type="SWING")
        self.description = "Positional setups: daily/weekly trends, S/R zones"
        self.timeframes = ['daily', 'weekly']
    
    def calculate_support_resistance(
        self,
        ohlc_data: List[Dict[str, float]],
        period: int = 20
    ) -> Dict[str, float]:
        """Calculate support/resistance levels."""
        if len(ohlc_data) < period:
            return {'support': 0, 'resistance': 0, 'pivot': 0}
        
        recent = ohlc_data[-period:]
        high = max(c['high'] for c in recent)
        low = min(c['low'] for c in recent)
        
        return {'support': low, 'resistance': high, 'pivot': (high + low) / 2}
    
    @log_execution_time
    @validate_symbol
    def analyze(self, symbol: str, option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None, sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze swing patterns."""
        logger.info(f"Analyzing swing for {symbol}")
        
        if market_data is None:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="NO_SIGNAL",
                reasoning="No market data", metadata={},
                timestamp=datetime.now(), trade_type="SWING"
            )
        
        ohlc = market_data.get('ohlc_daily', [])
        if len(ohlc) < 20:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="NO_SIGNAL",
                reasoning="Insufficient data", metadata={},
                timestamp=datetime.now(), trade_type="SWING"
            )
        
        signals = []
        closes = [c['close'] for c in ohlc]
        current_price = closes[-1]
        
        # EMA Analysis
        ema20 = self._calculate_ema(closes, 20)
        ema50 = self._calculate_ema(closes, 50) if len(closes) >= 50 else ema20
        
        if current_price > ema20 > ema50:
            signals.append(("BUY", 25, "Bullish trend"))
        elif current_price < ema20 < ema50:
            signals.append(("SELL", 25, "Bearish trend"))
        
        # S/R Levels
        sr = self.calculate_support_resistance(ohlc)
        if abs(current_price - sr['support']) / sr['support'] < 0.02:
            signals.append(("BUY", 20, f"Support at {sr['support']:.0f}"))
        elif abs(current_price - sr['resistance']) / sr['resistance'] < 0.02:
            signals.append(("SELL", 20, f"Resistance at {sr['resistance']:.0f}"))
        
        # RSI
        rsi = self._calculate_rsi(closes)
        if rsi < 30:
            signals.append(("BUY", 15, f"RSI {rsi:.0f}"))
        elif rsi > 70:
            signals.append(("SELL", 15, f"RSI {rsi:.0f}"))
        
        # Volume
        volumes = [c['volume'] for c in ohlc]
        if np.mean(volumes[-5:]) > np.mean(volumes[-20:]) * 1.3:
            if closes[-1] > closes[-5]:
                signals.append(("BUY", 10, "Volume up"))
            else:
                signals.append(("SELL", 10, "Volume down"))
        
        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")
        
        if buy_score > sell_score * 1.4:
            signal = "BUY"
            confidence = min(45 + buy_score, 95)
        elif sell_score > buy_score * 1.4:
            signal = "SELL"
            confidence = min(45 + sell_score, 95)
        else:
            signal = "HOLD"
            confidence = 50
        
        logger.info(f"{symbol}: {signal} ({confidence}%)")
        
        return AgentResponse(
            agent_name=self.name, confidence=confidence, signal=signal,
            reasoning=" | ".join([s[2] for s in signals]),
            metadata={'ema20': ema20, 'ema50': ema50, **sr},
            timestamp=datetime.now(), trade_type="SWING"
        )
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA."""
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI."""
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))
