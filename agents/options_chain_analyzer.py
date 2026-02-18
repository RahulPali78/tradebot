"""Options Chain Analyzer Agent.

Analyzes option chain data including Greeks, PCR, OI buildup, IV skew, and max pain.
Specialized for NSE India options market.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
try:
    from agents.base_agent import BaseAgent, AgentResponse
except ImportError:
    from base_agent import BaseAgent, AgentResponse


class OptionsChainAnalyzer(BaseAgent):
    """Analyzes option chain metrics for trading signals."""
    
    def __init__(self):
        super().__init__(name="OptionsChainAnalyzer", trade_type="BOTH")
        self.description = "Analyzes option Greeks, PCR, OI changes, IV, and max pain"
    
    def analyze(self, symbol: str,
                option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None,
                sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze option chain data and return confidence score."""
        
        metadata = {}
        signals = []
        confidence = 50.0
        
        if option_chain is None:
            return AgentResponse(
                agent_name=self.name,
                confidence=0,
                signal="NO_SIGNAL",
                reasoning="No option chain data provided",
                metadata={},
                timestamp=datetime.now(),
                trade_type="INRTRADAY"
            )
        
        # 1. Put-Call Ratio Analysis
        pcr = option_chain.get('pcr', 1.0)
        metadata['pcr'] = pcr
        
        if pcr > 1.3:
            signals.append(("BUY", 15, "PCR > 1.3 indicates extreme bearish sentiment - contrarian bullish"))
        elif pcr < 0.7:
            signals.append(("SELL", 15, "PCR < 0.7 indicates extreme bullish sentiment - contrarian bearish"))
        else:
            signals.append(("HOLD", 5, "PCR in neutral zone"))
        
        # 2. Open Interest Analysis
        oi_change = option_chain.get('oi_change_pct', 0)
        metadata['oi_change_pct'] = oi_change
        
        if oi_change > 10:
            signals.append(("BUY", 10, "Strong OI buildup suggests institutional interest"))
        elif oi_change < -10:
            signals.append(("SELL", 10, "OI unwinding suggests weaker hands"))
        
        # 3. IV Analysis (Implied Volatility)
        iv_current = option_chain.get('iv_current', 20)
        iv_percentile = option_chain.get('iv_percentile', 50)
        metadata['iv_current'] = iv_current
        metadata['iv_percentile'] = iv_percentile
        
        if iv_percentile > 80:
            signals.append(("SELL", 10, "IV in top 20% - expensive options, favor selling strategies"))
        elif iv_percentile < 20:
            signals.append(("BUY", 10, "IV in bottom 20% - cheap options, favor buying strategies"))
        
        # 4. Max Pain Analysis
        max_pain = option_chain.get('max_pain', 0)
        spot = option_chain.get('spot_price', 0)
        metadata['max_pain'] = max_pain
        metadata['spot_price'] = spot
        
        if spot < max_pain * 0.98:
            signals.append(("BUY", 10, "Spot below max pain - upward magnet toward expiry"))
        elif spot > max_pain * 1.02:
            signals.append(("SELL", 10, "Spot above max pain - downward magnet toward expiry"))
        
        # 5. Greeks Analysis (simplified)
        delta = option_chain.get('delta', 0.5)
        theta = option_chain.get('theta', -0.1)
        
        metadata['delta'] = delta
        metadata['theta'] = theta
        
        if abs(delta) > 0.7:
            signals.append(("HOLD", 5, "High delta - directional exposure is high"))
        
        # Calculate weighted score
        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")
        
        if buy_score > sell_score * 1.5:
            final_signal = "BUY"
            confidence = min(50 + buy_score, 95)
        elif sell_score > buy_score * 1.5:
            final_signal = "SELL"
            confidence = min(50 + sell_score, 95)
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
            trade_type="INTRADAY" if self.trade_type == "BOTH" else self.trade_type
        )
    
    def calculate_max_pain(self, strikes: list, call_oi: list, put_oi: list) -> float:
        """Calculate max pain (strike where maximum option buyers lose money)."""
        max_pain_val = 0
        max_pain_strike = strikes[0]
        
        for strike in strikes:
            pain = 0
            for i, s in enumerate(strikes):
                if s < strike:
                    pain += call_oi[i] * (strike - s)
                elif s > strike:
                    pain += put_oi[i] * (s - strike)
            
            if pain > max_pain_val:
                max_pain_val = pain
                max_pain_strike = strike
        
        return max_pain_strike
