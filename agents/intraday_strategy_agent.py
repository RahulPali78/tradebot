"""Intraday Strategy Agent."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np

from utils.decorators import validate_symbol, log_execution_time
from utils.logger import get_logger

from agents.base_agent import BaseAgent, AgentResponse

logger = get_logger('intraday_agent')


class IntradayStrategyAgent(BaseAgent):
    """Generates intraday trading signals based on technical analysis."""
    
    def __init__(self):
        super().__init__(name="IntradayStrategyAgent", trade_type="INTRADAY")
        self.description = "Short-term setups: VWAP, ORB, support/resistance, momentum"
        self.timeframes = ['15min', '30min', '1h']
    
    def is_optimal_entry_time(self, current_time: datetime) -> bool:
        """Only trade during optimal hours (10 AM - 2 PM IST)."""
        hour = current_time.hour
        return 10 <= hour < 14
    
    @log_execution_time
    @validate_symbol
    def analyze(self, symbol: str, option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None, sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze intraday patterns."""
        current_time = datetime.now()
        logger.info(f"Analyzing intraday for {symbol}")
        
        if not self.is_optimal_entry_time(current_time):
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="HOLD",
                reasoning=f"Suboptimal time ({current_time.hour}:00)",
                metadata={'hour': current_time.hour},
                timestamp=current_time, trade_type="INTRADAY"
            )
        
        signals = []
        if market_data is None or not market_data.get('ohlc_intraday'):
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="NO_SIGNAL",
                reasoning="No market data", metadata={},
                timestamp=datetime.now(), trade_type="INTRADAY"
            )
        
        ohlc = market_data['ohlc_intraday']
        closes = [c['close'] for c in ohlc]
        if len(closes) < 5:
            return AgentResponse(
                agent_name=self.name, confidence=0, signal="NO_SIGNAL",
                reasoning="Insufficient data", metadata={},
                timestamp=datetime.now(), trade_type="INTRADAY"
            )
        
        highs = [c['high'] for c in ohlc]
        lows = [c['low'] for c in ohlc]
        volumes = [c['volume'] for c in ohlc]
        current_price = closes[-1]
        
        # VWAP
        vwap = self._calculate_vwap(ohlc)
        if current_price > vwap * 1.005:
            signals.append(("BUY", 20, "Above VWAP"))
        elif current_price < vwap * 0.995:
            signals.append(("SELL", 20, "Below VWAP"))
        
        # ORB
        orb = self._analyze_orb(ohlc)
        if orb in ["BUY", "SELL"]:
            signals.append((orb, 25, "ORB breakout"))
        
        # Volume spike
        avg_vol = np.mean(volumes[-10:] if len(volumes) >= 10 else volumes)
        if volumes[-1] > avg_vol * 1.5:
            trend = "BUY" if closes[-1] > closes[-2] else "SELL"
            signals.append((trend, 15, "Volume spike"))
        
        # Support/Resistance
        for level in market_data.get('support_levels', [])[:3]:
            if abs(current_price - level) / level < 0.005:
                signals.append(("BUY", 20, f"Support at {level}"))
                break
        
        for level in market_data.get('resistance_levels', [])[:3]:
            if abs(current_price - level) / level < 0.005:
                signals.append(("SELL", 20, f"Resistance at {level}"))
                break
        
        # RSI
        rsi = self._calculate_rsi(closes)
        if rsi < 30:
            signals.append(("BUY", 10, f"RSI {rsi:.1f}"))
        elif rsi > 70:
            signals.append(("SELL", 10, f"RSI {rsi:.1f}"))
        
        # Calculate score
        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")
        
        if buy_score > sell_score * 1.3:
            signal = "BUY"
            confidence = min(40 + buy_score, 95)
        elif sell_score > buy_score * 1.3:
            signal = "SELL"
            confidence = min(40 + sell_score, 95)
        else:
            signal = "HOLD"
            confidence = 50
        
        logger.info(f"{symbol}: {signal} ({confidence}%)")
        
        return AgentResponse(
            agent_name=self.name, confidence=confidence, signal=signal,
            reasoning=" | ".join([s[2] for s in signals]),
            metadata={'vwap': vwap, 'rsi': rsi}, timestamp=datetime.now(),
            trade_type="INTRADAY"
        )
    
    def _calculate_vwap(self, ohlc: List[Dict]) -> float:
        """Calculate VWAP."""
        tp_vol, vol_sum = [], 0
        for bar in ohlc:
            tp = (bar['high'] + bar['low'] + bar['close']) / 3
            vol = bar['volume']
            tp_vol.append(tp * vol)
            vol_sum += vol
        return sum(tp_vol) / vol_sum if vol_sum > 0 else 0
    
    def _analyze_orb(self, ohlc: List[Dict], bars: int = 5) -> str:
        """Analyze Opening Range Breakout."""
        if len(ohlc) < bars + 3:
            return "HOLD"
        opening_high = max(c['high'] for c in ohlc[:bars])
        opening_low = min(c['low'] for c in ohlc[:bars])
        for candle in ohlc[bars:bars+3]:
            if candle['close'] > opening_high:
                return "BUY"
            elif candle['close'] < opening_low:
                return "SELL"
        return "HOLD"
    
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
