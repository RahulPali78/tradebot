"""Tests for agents."""
import unittest
from unittest.mock import Mock, patch
import sys
sys.path.append('/data/.openclaw/workspace/tradebot')

from agents.options_chain_analyzer import OptionsChainAnalyzer
from agents.intraday_strategy_agent import IntradayStrategyAgent
from agents.swing_strategy_agent import SwingStrategyAgent
from agents.sentiment_scout import SentimentScout
from agents.risk_manager import RiskManager


class TestOptionsChainAnalyzer(unittest.TestCase):
    """Test OptionsChainAnalyzer."""
    
    def setUp(self):
        self.analyzer = OptionsChainAnalyzer()
    
    def test_suggest_optimal_strike_high_volatility(self):
        """Test strike suggestion in high volatility."""
        self.analyzer.iv_rank = 80
        strike = self.analyzer.suggest_optimal_strike(18000, "CALL")
        # High vol should suggest OTM
        self.assertGreater(strike, 18000)
    
    def test_suggest_optimal_strike_low_volatility(self):
        """Test strike suggestion in low volatility."""
        self.analyzer.iv_rank = 30
        strike = self.analyzer.suggest_optimal_strike(18000, "CALL")
        # Low vol should stick to ATM
        self.assertEqual(strike, 18000)


class TestIntradayStrategyAgent(unittest.TestCase):
    """Test IntradayStrategyAgent."""
    
    def setUp(self):
        self.agent = IntradayStrategyAgent()
    
    def test_is_optimal_entry_time(self):
        """Test time-based filtering."""
        from datetime import datetime
        
        # Optimal time (10 AM - 2 PM)
        optimal_time = datetime(2025, 1, 1, 11, 0, 0)
        self.assertTrue(self.agent.is_optimal_entry_time(optimal_time))
        
        # Non-optimal time (before 10 AM)
        suboptimal_time = datetime(2025, 1, 1, 9, 0, 0)
        self.assertFalse(self.agent.is_optimal_entry_time(suboptimal_time))


class TestSwingStrategyAgent(unittest.TestCase):
    """Test SwingStrategyAgent."""
    
    def setUp(self):
        self.agent = SwingStrategyAgent()
    
    def test_calculate_support_resistance(self):
        """Test S/R calculation."""
        ohlc_data = [
            {'high': 100, 'low': 90, 'close': 95},
            {'high': 105, 'low': 92, 'close': 98},
            {'high': 110, 'low': 88, 'close': 100},
        ]
        
        result = self.agent.calculate_support_resistance(ohlc_data)
        self.assertIn('support', result)
        self.assertIn('resistance', result)
        self.assertEqual(result['resistance'], 110)
        self.assertEqual(result['support'], 88)


class TestSentimentScout(unittest.TestCase):
    """Test SentimentScout."""
    
    def setUp(self):
        self.scout = SentimentScout()
    
    def test_sentiment_neutral(self):
        """Test neutral sentiment."""
        sentiment = self.scout.get_sentiment("NIFTY")
        self.assertIn(sentiment, ['BULLISH', 'BEARISH', 'NEUTRAL'])


class TestRiskManager(unittest.TestCase):
    """Test RiskManager."""
    
    def setUp(self):
        self.manager = RiskManager(max_exposure=100000)
    
    def test_check_position_correlation(self):
        """Test position correlation check."""
        existing = ['NIFTY']
        valid, msg = self.manager.check_position_correlation('BANKNIFTY', existing)
        # NIFTY and BANKNIFTY have 0.8 correlation
        self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main()
