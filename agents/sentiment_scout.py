"""Sentiment Scout Agent.

Monitors market sentiment through FII/DII flows, global cues, news sentiment, and macro factors.
Specialized for NSE India market conditions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentResponse


class SentimentScout(BaseAgent):
    """Monitors market sentiment and macro signals."""
    
    def __init__(self):
        super().__init__(name="SentimentScout", trade_type="BOTH")
        self.description = "FII/DII flows, global cues, news sentiment, INR/USD, crude"
    
    def analyze(self, symbol: str,
                option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None,
                sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze market sentiment and return confidence score."""
        
        metadata = {}
        signals = []
        confidence = 50.0
        
        if sentiment_data is None:
            return AgentResponse(
                agent_name=self.name,
                confidence=50,
                signal="HOLD",
                reasoning="No sentiment data - neutral stance",
                metadata={},
                timestamp=datetime.now(),
                trade_type="INTRADAY" if self.trade_type == "BOTH" else self.trade_type
            )
        
        # 1. FII/DII Flow Analysis
        fii_flow = sentiment_data.get('fii_net_flow', 0)
        dii_flow = sentiment_data.get('dii_net_flow', 0)
        
        metadata['fii_flow'] = fii_flow
        metadata['dii_flow'] = dii_flow
        
        if fii_flow > 500:  # Crores
            signals.append(("BUY", 15, f"Strong FII buying: ₹{fii_flow} Cr"))
        elif fii_flow < -500:
            signals.append(("SELL", 15, f"Strong FII selling: ₹{abs(fii_flow)} Cr"))
        
        # FII + DII divergence
        if fii_flow > 0 and dii_flow < 0:
            signals.append(("HOLD", 5, "FII buying vs DII selling - mixed signals"))
        elif fii_flow < 0 and dii_flow > 0:
            signals.append(("BUY", 10, "DII absorbing FII selling - local support"))
        
        # 2. Global Cues
        global_cues = sentiment_data.get('global_cues', {})
        
        # US Futures
        dow_futures = global_cues.get('dow_futures', 0)
        nasdaq_futures = global_cues.get('nasdaq_futures', 0)
        
        metadata['dow_futures'] = dow_futures
        metadata['nasdaq_futures'] = nasdaq_futures
        
        if dow_futures > 0.5 and nasdaq_futures > 0.5:
            signals.append(("BUY", 10, f"US futures up: Dow {dow_futures}%, NQ {nasdaq_futures}%"))
        elif dow_futures < -0.5 and nasdaq_futures < -0.5:
            signals.append(("SELL", 10, f"US futures down: Dow {dow_futures}%, NQ {nasdaq_futures}%"))
        
        # Asian Markets (SGX Nifty)
        sgx_nifty = global_cues.get('sgx_nifty', 0)
        metadata['sgx_nifty'] = sgx_nifty
        
        if sgx_nifty > 50:
            signals.append(("BUY", 15, f"SGX Nifty +{sgx_nifty} points - positive premarket"))
        elif sgx_nifty < -50:
            signals.append(("SELL", 15, f"SGX Nifty {sgx_nifty} points - negative premarket"))
        
        # 3. Commodity Cues
        crude = sentiment_data.get('crude_oil', 0)
        gold = sentiment_data.get('gold', 0)
        
        metadata['crude_usd'] = crude
        metadata['gold_usd'] = gold
        
        # Crude impact on Indian market
        if crude > 85:  # High crude negative for India
            signals.append(("SELL", 10, f"High crude ${crude} - import bill pressure"))
        elif crude < 70:
            signals.append(("BUY", 10, f"Low crude ${crude} - positive for India"))
        
        # 4. INR/USD Rate
        inr_usd = sentiment_data.get('inr_usd', 83.0)
        metadata['inr_usd'] = inr_usd
        
        if inr_usd > 84:
            signals.append(("SELL", 10, f"Weak INR {inr_usd} - capital flight risk"))
        elif inr_usd < 82:
            signals.append(("BUY", 10, f"Strong INR {inr_usd} - positive for flows"))
        
        # 5. News Sentiment
        news_sentiment = sentiment_data.get('news_sentiment', 'neutral')
        news_score = sentiment_data.get('news_sentiment_score', 0)
        
        metadata['news_sentiment'] = news_sentiment
        metadata['news_score'] = news_score
        
        if news_sentiment == 'positive' and news_score > 0.6:
            signals.append(("BUY", 15, f"Positive news sentiment: {news_score:.0%}"))
        elif news_sentiment == 'negative' and news_score < -0.6:
            signals.append(("SELL", 15, f"Negative news sentiment: {abs(news_score):.0%}"))
        elif sentiment_data.get('breaking_news', '').lower().find('rate cut') != -1:
            signals.append(("BUY", 20, "Rate cut news - bullish for equities"))
        elif sentiment_data.get('breaking_news', '').lower().find('rate hike') != -1:
            signals.append(("SELL", 20, "Rate hike news - bearish for equities"))
        
        # 6. VIX Analysis (Volatility)
        vix = sentiment_data.get('vix', 15)
        metadata['vix'] = vix
        
        if vix > 20:
            signals.append(("HOLD", 5, f"High VIX {vix} - caution advised"))
        elif vix < 12:
            signals.append(("BUY", 10, f"Low VIX {vix} - complacency, opportunity for breakout"))
        
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
        
        reasoning = " | ".join([s[2] for s in signals]) if signals else "Neutral sentiment - no strong signals"
        
        return AgentResponse(
            agent_name=self.name,
            confidence=confidence,
            signal=final_signal,
            reasoning=reasoning,
            metadata=metadata,
            timestamp=datetime.now(),
            trade_type="INTRADAY" if self.trade_type == "BOTH" else self.trade_type
        )
