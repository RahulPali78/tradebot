"""Intraday Strategy Agent.

Analyzes short-term setups for options scalping and day trading.
Focuses on 15/30min patterns, VWAP, Opening Range Breakout (ORB), and key levels.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
from .base_agent import BaseAgent, AgentResponse


class IntradayStrategyAgent(BaseAgent):
    """Generates intraday trading signals based on technical analysis."""
    
    def __init__(self):
        super().__init__(name="IntradayStrategyAgent", trade_type="INTRADAY")
        self.description = "Short-term setups: VWAP, ORB, support/resistance, momentum"
        self.timeframes = ['15min', '30min', '1h']
    
    def analyze(self, symbol: str,
                option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None,
                sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze intraday patterns and return confidence score."""
        
        metadata = {}
        signals = []
        confidence = 50.0
        
        if market_data is None:
            return AgentResponse(
                agent_name=self.name,
                confidence=0,
                signal="NO_SIGNAL",
                reasoning="No market data provided for intraday analysis",
                metadata={},
                timestamp=datetime.now(),
                trade_type="INTRADAY"
            )
        
        # Get OHLC data
        ohlc = market_data.get('ohlc_intraday', [])
        if not ohlc:
            return AgentResponse(
                agent_name=self.name,
                confidence=0,
                signal="NO_SIGNAL",
                reasoning="No intraday OHLC data available",
                metadata={},
                timestamp=datetime.now(),
                trade_type="INTRADAY"
            )
        
        closes = [c['close'] for c in ohlc]
        highs = [c['high'] for c in ohlc]
        lows = [c['low'] for c in ohlc]
        volumes = [c['volume'] for c in ohlc]
        
        current_price = closes[-1] if closes else 0
        metadata['current_price'] = current_price
        
        # 1. VWAP Analysis
        vwap = self._calculate_vwap(ohlc)
        metadata['vwap'] = vwap
        
        if current_price > vwap * 1.005:
            signals.append(("BUY", 20, f"Price {current_price:.2f} above VWAP {vwap:.2f} - bullish"))
        elif current_price < vwap * 0.995:
            signals.append(("SELL", 20, f"Price {current_price:.2f} below VWAP {vwap:.2f} - bearish"))
        else:
            signals.append(("HOLD", 5, "Price near VWAP - neutral"))
        
        # 2. Opening Range Breakout (ORB)
        orb_signal = self._analyze_orb(ohlc)
        if orb_signal == "BUY":
            signals.append(("BUY", 25, "Opening Range Breakout - bullish momentum"))
        elif orb_signal == "SELL":
            signals.append(("SELL", 25, "Opening Range Breakdown - bearish momentum"))
        
        # 3. Volume Confirmation
        avg_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else np.mean(volumes)
        current_volume = volumes[-1] if volumes else 0
        metadata['avg_volume'] = avg_volume
        metadata['current_volume'] = current_volume
        
        if current_volume > avg_volume * 1.5:
            signals.append(("BUY" if closes[-1] > closes[-2] else "SELL", 15, 
                          f"Volume spike {current_volume/avg_volume:.1f}x avg - confirming"))
        
        # 4. Support/Resistance Bounce
        supports = market_data.get('support_levels', [])
        resistances = market_data.get('resistance_levels', [])
        
        metadata['support_levels'] = supports
        metadata['resistance_levels'] = resistances
        
        for support in supports:
            if abs(current_price - support) / support < 0.005:
                signals.append(("BUY", 20, f"Support bounce at {support}"))
                break
        
        for resistance in resistances:
            if abs(current_price - resistance) / resistance < 0.005:
                signals.append(("SELL", 20, f"Resistance rejection at {resistance}"))
                break
        
        # 5. RSI Divergence (simplified)
        rsi = self._calculate_rsi(closes)
        metadata['rsi'] = rsi
        
        if rsi < 30:
            signals.append(("BUY", 10, f"RSI oversold {rsi:.1f} - potential bounce"))
        elif rsi > 70:
            signals.append(("SELL", 10, f"RSI overbought {rsi:.1f} - potential pullback"))
        
        # Calculate final signal
        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")
        
        if buy_score > sell_score * 1.3:
            final_signal = "BUY"
            confidence = min(40 + buy_score, 95)
        elif sell_score > buy_score * 1.3:
            final_signal = "SELL"
            confidence = min(40 + sell_score, 95)
        else:
            final_signal = "HOLD"
            confidence = 50
        
        reasoning = " | ".join([s[2] for s in signals])
        
        return AgentResponse(
            agent_name=self.name,
            confidence=confidence,
            signal=final_signal,
            reasoning=reasoning,
            metadata=metadata,
            timestamp=datetime.now(),
            trade_type="INTRADAY"
        )
    
    def _calculate_vwap(self, ohlc: List[Dict]) -> float:
        """Calculate VWAP from OHLC data."""
        typical_price_volume = []
        volume_sum = 0
        
        for bar in ohlc:
            tp = (bar['high'] + bar['low'] + bar['close']) / 3
            vol = bar['volume']
            typical_price_volume.append(tp * vol)
            volume_sum += vol
        
        return sum(typical_price_volume) / volume_sum if volume_sum > 0 else 0
    
    def _analyze_orb(self, ohlc: List[Dict], bars: int = 5) -> str:
        """Analyze Opening Range Breakout."""
        if len(ohlc) < bars + 5:
            return "HOLD"
        
        # First N bars define the opening range
        opening_high = max(c['high'] for c in ohlc[:bars])
        opening_low = min(c['low'] for c in ohlc[:bars])
        
        # Check for breakout after opening range
        recent_candles = ohlc[bars:bars+5]
        for candle in recent_candles:
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
        
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
