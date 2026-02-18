"""Swing Strategy Agent.

Analyzes positional setups for swing trading options.
Focuses on daily/weekly trends, support/resistance zones, and option spreads.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np
from .base_agent import BaseAgent, AgentResponse


class SwingStrategyAgent(BaseAgent):
    """Generates swing trading signals based on positional analysis."""
    
    def __init__(self):
        super().__init__(name="SwingStrategyAgent", trade_type="SWING")
        self.description = "Positional setups: daily/weekly trends, S/R zones, spreads"
        self.timeframes = ['daily', 'weekly']
    
    def analyze(self, symbol: str,
                option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None,
                sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze swing patterns and return confidence score."""
        
        metadata = {}
        signals = []
        confidence = 50.0
        
        if market_data is None:
            return AgentResponse(
                agent_name=self.name,
                confidence=0,
                signal="NO_SIGNAL",
                reasoning="No market data provided for swing analysis",
                metadata={},
                timestamp=datetime.now(),
                trade_type="SWING"
            )
        
        # Get daily OHLC data
        ohlc_daily = market_data.get('ohlc_daily', [])
        if len(ohlc_daily) < 20:
            return AgentResponse(
                agent_name=self.name,
                confidence=0,
                signal="NO_SIGNAL",
                reasoning="Insufficient daily data for swing analysis",
                metadata={},
                timestamp=datetime.now(),
                trade_type="SWING"
            )
        
        closes = [c['close'] for c in ohlc_daily]
        highs = [c['high'] for c in ohlc_daily]
        lows = [c['low'] for c in ohlc_daily]
        volumes = [c['volume'] for c in ohlc_daily]
        
        current_price = closes[-1]
        metadata['current_price'] = current_price
        
        # 1. Trend Analysis (higher timeframe)
        ema20 = self._calculate_ema(closes, 20)
        ema50 = self._calculate_ema(closes, 50) if len(closes) >= 50 else ema20
        
        metadata['ema20'] = ema20
        metadata['ema50'] = ema50
        
        if current_price > ema20 > ema50:
            signals.append(("BUY", 25, f"Bullish trend: Price > EMA20 > EMA50"))
        elif current_price < ema20 < ema50:
            signals.append(("SELL", 25, f"Bearish trend: Price < EMA20 < EMA50"))
        else:
            signals.append(("HOLD", 5, "Mixed trend signals"))
        
        # 2. Support/Resistance Zones (weekly levels)
        weekly_high = max(highs[-20:])
        weekly_low = min(lows[-20:])
        
        metadata['weekly_high'] = weekly_high
        metadata['weekly_low'] = weekly_low
        
        if abs(current_price - weekly_low) / weekly_low < 0.02:
            signals.append(("BUY", 20, f"Near weekly support {weekly_low:.2f}"))
        elif abs(current_price - weekly_high) / weekly_high < 0.02:
            signals.append(("SELL", 20, f"Near weekly resistance {weekly_high:.2f}"))
        
        # 3. Volume Analysis (accumulation/distribution)
        avg_volume = np.mean(volumes[-20:])
        recent_volume = np.mean(volumes[-5:])
        
        metadata['avg_volume'] = avg_volume
        metadata['recent_volume'] = recent_volume
        
        if recent_volume > avg_volume * 1.3:
            if closes[-1] > closes[-5]:
                signals.append(("BUY", 15, "High volume + price rise = accumulation"))
            else:
                signals.append(("SELL", 15, "High volume + price drop = distribution"))
        
        # 4. RSI and Divergence (daily)
        rsi = self._calculate_rsi(closes)
        metadata['rsi'] = rsi
        
        if rsi < 30 and closes[-1] > np.mean(closes[-5:]):
            signals.append(("BUY", 20, f"RSI {rsi:.1f} oversold with price recovery"))
        elif rsi > 70 and closes[-1] < np.mean(closes[-5:]):
            signals.append(("SELL", 20, f"RSI {rsi:.1f} overbought with price weakness"))
        
        # 5. Option Spread Recommendation
        iv = option_chain.get('iv_current', 20) if option_chain else 20
        metadata['suggested_spread'] = self._suggest_spread(current_price, iv, ema20, ema50)
        
        # Calculate final signal
        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")
        
        if buy_score > sell_score * 1.4:
            final_signal = "BUY"
            confidence = min(45 + buy_score, 95)
        elif sell_score > buy_score * 1.4:
            final_signal = "SELL"
            confidence = min(45 + sell_score, 95)
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
            trade_type="SWING"
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
        
        avg_gain = np.mean(gains) if gains else 0.001
        avg_loss = np.mean(losses) if losses else 0.001
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _suggest_spread(self, price: float, iv: float, ema20: float, ema50: float) -> str:
        """Suggest option spread strategy based on market conditions."""
        bullish = price > ema20 > ema50
        bearish = price < ema20 < ema50
        high_iv = iv > 25
        
        if bullish and not high_iv:
            return "Long Call or Bull Call Spread"
        elif bullish and high_iv:
            return "Bull Put Spread (credit)"
        elif bearish and not high_iv:
            return "Long Put or Bear Put Spread"
        elif bearish and high_iv:
            return "Bear Call Spread (credit)"
        else:
            return "Iron Condor (neutral)"
