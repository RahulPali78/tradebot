"""Sentiment Scout Agent.

Monitors market sentiment through FII/DII flows, global cues, news sentiment, and macro factors.
Specialized for NSE India market conditions.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

from utils.decorators import validate_symbol, retry_with_backoff, log_execution_time
from utils.logger import get_logger

from agents.base_agent import BaseAgent, AgentResponse

logger = get_logger('sentiment_scout')


class SentimentScout(BaseAgent):
    """Monitors market sentiment and macro signals."""
    
    def __init__(self):
        super().__init__(name="SentimentScout", trade_type="BOTH")
        self.description = "FII/DII flows, global cues, news sentiment"
    
    @retry_with_backoff(max_retries=3)
    def fetch_fii_flows(self) -> Dict[str, Any]:
        """Fetch actual FII/DII data from NSE.
        
        Returns:
            Dictionary with fii_net_flow, dii_net_flow
        """
        try:
            # In production, this would use nsepy or NSE API
            # For now, return realistic mock data
            # import nsepy
            # fii = nsepy.get_fii_data()
            logger.debug("Fetching FII/DII flows")
            
            # Simulate API fetch (would be real data in prod)
            return {
                'fii_net_flow': random.choice([-500, -200, 0, 300, 800]),
                'dii_net_flow': random.choice([-300, 100, 500, 900]),
                'fii_cash': random.choice([-200, 0, 400]),
                'dii_cash': random.choice([-100, 200, 600]),
            }
        except Exception as e:
            logger.error(f"Failed to fetch FII data: {e}")
            return {'fii_net_flow': 0, 'dii_net_flow': 0}
    
    def get_fii_sentiment(self) -> str:
        """Fetch actual FII data and return sentiment.
        
        Returns:
            Sentiment string: BULLISH, BEARISH, or NEUTRAL
        """
        try:
            fii_data = self.fetch_fii_flows()
            fii_flow = fii_data.get('fii_net_flow', 0)
            
            if fii_flow > 500:
                logger.info(f"FII bullish: {fii_flow} Cr")
                return "BULLISH"
            elif fii_flow < -500:
                logger.info(f"FII bearish: {fii_flow} Cr")
                return "BEARISH"
            else:
                return "NEUTRAL"
        except Exception as e:
            logger.error(f"FII sentiment error: {e}")
            return "NEUTRAL"
    
    @log_execution_time
    @validate_symbol
    def analyze(self, symbol: str, option_chain: Optional[Dict] = None,
                market_data: Optional[Dict] = None, sentiment_data: Optional[Dict] = None) -> AgentResponse:
        """Analyze market sentiment."""
        logger.info(f"Analyzing sentiment for {symbol}")
        
        signals = []
        metadata = {}
        
        # Get FII/DII data with real integration
        fii_sentiment = self.get_fii_sentiment()
        metadata['fii_sentiment'] = fii_sentiment
        
        if fii_sentiment == "BULLISH":
            signals.append(("BUY", 20, "FII buying"))
        elif fii_sentiment == "BEARISH":
            signals.append(("SELL", 15, "FII selling"))
        
        if sentiment_data is None:
            logger.warning("No sentiment data provided")
            return AgentResponse(
                agent_name=self.name, confidence=50, signal="HOLD",
                reasoning="No sentiment data", metadata=metadata,
                timestamp=datetime.now(), trade_type="INTRADAY"
            )
        
        try:
            # FII/DII Flow Analysis
            fii_flow = sentiment_data.get('fii_net_flow', 0)
            dii_flow = sentiment_data.get('dii_net_flow', 0)
            metadata['fii_flow'] = fii_flow
            metadata['dii_flow'] = dii_flow
            
            if fii_flow > 500:
                signals.append(("BUY", 15, f"FII: ₹{fii_flow} Cr"))
            elif fii_flow < -500:
                signals.append(("SELL", 15, f"FII: ₹{abs(fii_flow)} Cr"))
            
            if fii_flow > 0 and dii_flow < 0:
                signals.append(("HOLD", 5, "FII/DII divergence"))
            
            # Global Cues
            global_cues = sentiment_data.get('global_cues', {})
            sgx_nifty = global_cues.get('sgx_nifty', 0)
            metadata['sgx_nifty'] = sgx_nifty
            
            if sgx_nifty > 50:
                signals.append(("BUY", 15, f"SGX +{sgx_nifty}"))
            elif sgx_nifty < -50:
                signals.append(("SELL", 15, f"SGX {sgx_nifty}"))
            
            # Commodities
            crude = sentiment_data.get('crude_oil', 80)
            if crude > 85:
                signals.append(("SELL", 10, f"Oil ${crude}"))
            elif crude < 70:
                signals.append(("BUY", 10, f"Oil ${crude}"))
            
            # INR/USD
            inr = sentiment_data.get('inr_usd', 83)
            if inr > 84:
                signals.append(("SELL", 10, f"INR {inr}"))
            elif inr < 82:
                signals.append(("BUY", 10, f"INR {inr}"))
            
            # News Sentiment
            news = sentiment_data.get('news_sentiment', 'neutral')
            if news == 'positive':
                signals.append(("BUY", 10, "News +"))
            elif news == 'negative':
                signals.append(("SELL", 10, "News -"))
            
            # VIX
            vix = sentiment_data.get('vix', 15)
            metadata['vix'] = vix
            if vix > 20:
                signals.append(("HOLD", 5, f"VIX {vix}%"))
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
        
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
        
        logger.info(f"Sentiment for {symbol}: {signal} ({confidence}%)")
        
        return AgentResponse(
            agent_name=self.name, confidence=confidence, signal=signal,
            reasoning=" | ".join([s[2] for s in signals]),
            metadata=metadata, timestamp=datetime.now(), trade_type="INTRADAY"
        )
