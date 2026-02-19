"""NSE Options Trading Main Agent - Orchestrator."""
import yaml
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import setup_logging
from database.decision_logger import DecisionLogger
from database.trade_history import TradeHistory
from execution.trade_executor import TradeExecutor
from execution.alert_manager import AlertManager

from agents import (
    OptionsChainAnalyzer, IntradayStrategyAgent, SwingStrategyAgent,
    SentimentScout, RiskManager, MainDecisionAgent, AgentResponse
)

logger = logging.getLogger('tradebot')


class TradingOrchestrator:
    """Main orchestrator."""
    
    def __init__(self, config_path: str = "config.yaml"):
        setup_logging()
        self.config = self._load_config(config_path)
        
        self.decision_logger = DecisionLogger()
        self.trade_history = TradeHistory()
        self.trade_executor = TradeExecutor(trade_history=self.trade_history)
        self.alert_manager = AlertManager()
        
        self.agents = {
            'OptionsChainAnalyzer': OptionsChainAnalyzer(),
            'IntradayStrategyAgent': IntradayStrategyAgent(),
            'SwingStrategyAgent': SwingStrategyAgent(),
            'SentimentScout': SentimentScout(),
            'RiskManager': RiskManager(self.config.get('capital', 100000)),
            'MainDecisionAgent': MainDecisionAgent(config_path),
        }
        self.main_agent = self.agents['MainDecisionAgent']
        
        logger.info("TradingOrchestrator initialized")
    
    def _load_config(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def run_agents_in_parallel(self, symbol, option_chain, market_data, sentiment_data):
        responses = []
        
        def run_agent(name, agent):
            return name, agent.analyze(symbol, option_chain, market_data, sentiment_data)
        
        agents_to_run = [(n, a) for n, a in self.agents.items() if n != 'MainDecisionAgent']
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(run_agent, n, a): n for n, a in agents_to_run}
            for future in as_completed(futures):
                try:
                    name, response = future.result()
                    logger.info(f"  {name}: {response.signal} ({response.confidence:.0f}%)")
                    responses.append(response)
                except Exception as e:
                    logger.error(f"Agent error: {e}")
        
        return responses
    
    def analyze_symbol(self, symbol: str, trade_type: str = "INTRADAY"):
        symbol = symbol.upper()
        logger.info(f"Analyzing {symbol}")
        
        # Mock data
        option_chain = {'spot_price': 18000, 'pcr': 1.2}
        market_data = {'ohlc_intraday': [], 'ohlc_daily': []}
        sentiment_data = {'fii_net_flow': 300}
        
        responses = self.run_agents_in_parallel(symbol, option_chain, market_data, sentiment_data)
        decision = self.main_agent.aggregate(responses, trade_type)
        
        self.decision_logger.log_decision(symbol, decision.to_dict())
        
        if decision.confidence >= 70 and decision.signal in ['BUY', 'SELL']:
            try:
                self.trade_executor.execute_trade(
                    symbol=symbol,
                    signal=decision.signal,
                    quantity=50,
                    price=option_chain['spot_price'],
                    confidence=decision.confidence,
                    strategy=trade_type
                )
                self.alert_manager.send_trade_alert(symbol, decision.signal, decision.confidence)
            except Exception as e:
                logger.error(f"Trade execution failed: {e}")
        
        return {'decision': decision.to_dict(), 'agent_responses': [r.to_dict() for r in responses]}
    
    def run_scan(self, symbols=None):
        symbols = symbols or ['NIFTY', 'BANKNIFTY']
        results = {}
        for symbol in symbols:
            results[symbol] = self.analyze_symbol(symbol)
        return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', '-s')
    parser.add_argument('--scan', action='store_true')
    args = parser.parse_args()
    
    orch = TradingOrchestrator()
    if args.symbol:
        orch.analyze_symbol(args.symbol.upper())
    elif args.scan:
        orch.run_scan()
    else:
        orch.analyze_symbol("NIFTY")


if __name__ == "__main__":
    main()
