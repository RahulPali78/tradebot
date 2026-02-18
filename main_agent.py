"""NSE Options Trading Main Agent - Orchestrator.

Coordinates all specialist agents, runs the decision loop,
and outputs trade signals with 70%+ confidence threshold.
"""

import yaml
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Import all agents
from agents.options_chain_analyzer import OptionsChainAnalyzer
from agents.intraday_strategy_agent import IntradayStrategyAgent
from agents.swing_strategy_agent import SwingStrategyAgent
from agents.sentiment_scout import SentimentScout
from agents.risk_manager import RiskManager
from agents.main_decision_agent import MainDecisionAgent
from agents.base_agent import AgentResponse

# Import data fetchers
import sys
sys.path.append('data_sources')
from nse_data import NSEDataFetcher


class TradingOrchestrator:
    """Main orchestrator for the multi-agent trading system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the trading system."""
        self.config = self._load_config(config_path)
        self.data_fetcher = NSEDataFetcher()
        
        # Initialize all agents
        self.agents = {
            'OptionsChainAnalyzer': OptionsChainAnalyzer(),
            'IntradayStrategyAgent': IntradayStrategyAgent(),
            'SwingStrategyAgent': SwingStrategyAgent(),
            'SentimentScout': SentimentScout(),
            'RiskManager': RiskManager(),
            'MainDecisionAgent': MainDecisionAgent(config_path),
        }
        
        self.main_agent = self.agents['MainDecisionAgent']
        self.trade_history = []
        
        print(f"[{datetime.now()}] TradingOrchestrator initialized")
        print(f"  Capital: ₹{self.config['capital_allocation']['total_capital']:,}")
        print(f"  Intraday: {self.config['capital_allocation']['intraday_allocation_pct']}%")
        print(f"  Swing: {self.config['capital_allocation']['swing_allocation_pct']}%")
        print(f"  Threshold: {self.config['decision']['min_probability_threshold']*100:.0f}%")
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def analyze_symbol(self, symbol: str, trade_type: str = "INTRADAY") -> Dict[str, Any]:
        """Run full analysis on a symbol."""
        
        print(f"\n{'='*60}")
        print(f"Analyzing {symbol} | Trade Type: {trade_type}")
        print(f"{'='*60}")
        
        # Fetch all required data
        print("[1/3] Fetching market data...")
        option_chain = self.data_fetcher.get_option_chain(symbol)
        market_data = self.data_fetcher.get_intraday_data(symbol)
        sentiment_data = self.data_fetcher.get_sentiment_data()
        
        if trade_type == "SWING":
            market_data.update(self.data_fetcher.get_daily_data(symbol))
        
        # Run specialist agents
        print(f"[2/3] Running {len(self.agents)-1} specialist agents...")
        agent_responses = []
        
        for name, agent in self.agents.items():
            if name == 'MainDecisionAgent':
                continue
            
            response = agent.analyze(
                symbol=symbol,
                option_chain=option_chain,
                market_data=market_data,
                sentiment_data=sentiment_data
            )
            
            agent_responses.append(response)
            print(f"  ✓ {name}: {response.signal} ({response.confidence:.0f}%)")
        
        # Run main decision agent
        print("[3/3] Aggregating signals...")
        decision = self.main_agent.aggregate(agent_responses, trade_type)
        
        # Output result
        print(f"\n{'='*60}")
        print(f"FINAL DECISION: {decision.signal}")
        print(f"Confidence: {decision.confidence:.1f}%")
        print(f"Threshold: {self.config['decision']['min_probability_threshold']*100:.0f}%")
        print(f"Execute: {'YES' if decision.confidence >= 70 else 'NO'}")
        print(f"{'='*60}")
        print(f"Reasoning: {decision.reasoning[:200]}...")
        
        # Store trade if executed
        if decision.confidence >= 70 and decision.signal in ['BUY', 'SELL']:
            self.trade_history.append({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'signal': decision.signal,
                'confidence': decision.confidence,
                'trade_type': trade_type,
            })
        
        return {
            'decision': decision.to_dict(),
            'agent_responses': [r.to_dict() for r in agent_responses],
            'data_snapshot': {
                'spot_price': option_chain.get('spot_price'),
                'pcr': option_chain.get('pcr'),
                'iv': option_chain.get('iv_current'),
            }
        }
    
    def run_scan(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Scan multiple symbols for trade opportunities."""
        
        if symbols is None:
            symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        
        results = {}
        opportunities = []
        
        for symbol in symbols:
            result = self.analyze_symbol(symbol, trade_type="INTRADAY")
            results[symbol] = result
            
            if result['decision']['confidence'] >= 70:
                opportunities.append({
                    'symbol': symbol,
                    'signal': result['decision']['signal'],
                    'confidence': result['decision']['confidence'],
                })
        
        print(f"\n{'='*60}")
        print(f"SCAN COMPLETE")
        print(f"{'='*60}")
        print(f"Symbols scanned: {len(symbols)}")
        print(f"Opportunities found: {len(opportunities)}")
        
        for opp in opportunities:
            print(f"  → {opp['symbol']}: {opp['signal']} ({opp['confidence']:.0f}%)")
        
        return {
            'results': results,
            'opportunities': opportunities,
            'scan_time': datetime.now().isoformat(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            'decision_stats': self.main_agent.get_decision_stats(),
            'trade_history': self.trade_history,
            'total_trades': len(self.trade_history),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='NSE Options Trading Multi-Agent System')
    parser.add_argument('--symbol', '-s', help='Symbol to analyze')
    parser.add_argument('--scan', action='store_true', help='Scan default symbols')
    parser.add_argument('--swing', action='store_true', help='Use swing trading mode')
    
    args = parser.parse_args()
    
    orchestrator = TradingOrchestrator()
    
    if args.symbol:
        trade_type = "SWING" if args.swing else "INTRADAY"
        orchestrator.analyze_symbol(args.symbol.upper(), trade_type)
    elif args.scan:
        orchestrator.run_scan()
    else:
        # Default: demo mode
        print("Running in demo mode...")
        orchestrator.analyze_symbol("NIFTY", "INTRADAY")


if __name__ == "__main__":
    main()
