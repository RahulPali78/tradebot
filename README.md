# NSE Options Trading Multi-Agent System

A multi-agent trading system for NSE India options trading. Specialist agents analyze different market aspects, and the main agent aggregates their signals with a **70%+ confidence threshold** for trade execution.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TradingOrchestrator                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         │      Specialist Agents        │
         └───────────────────────────────┘
                        │
    ┌───────────┬───────┴───────┬───────────┬───────────┐
    │           │               │           │           │
    ▼           ▼               ▼           ▼           ▼
┌───────┐  ┌────────┐      ┌────────┐  ┌────────┐  ┌────────┐
│Options│  │Intraday│      │ Swing  │  │Sentiment│  │  Risk  │
│Chain  │  │Strategy│      │Strategy│  │ Scout  │  │Manager │
│Analyzer│  │ Agent  │      │ Agent  │  │        │  │        │
└───┬────┘  └───┬────┘      └───┬────┘  └───┬────┘  └───┬────┘
    │           │               │           │           │
    │           │               │           │           │
    └───────────┴───────────────┴───────────┴───────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ MainDecisionAgent │
                   └────────┬────────┘
                            │
                            │ >70% threshold?
                   ┌────────┴────────┐
                   │   YES  │  NO    │
                   ▼        ▼         ▼
              ┌────────┐ ┌────────┐ ┌────────┐
              │ EXECUTE│ │ HOLD   │ │ REJECT │
              │  TRADE │ │        │ │        │
              └────────┘ └────────┘ └────────┘
```

## Specialist Agents

| Agent | Weight | Focus |
|-------|--------|-------|
| **OptionsChainAnalyzer** | 25% | Greeks, PCR, OI buildup, IV, max pain |
| **IntradayStrategyAgent** | 20% | VWAP, ORB, S/R levels, 15/30min setups |
| **SwingStrategyAgent** | 20% | Daily/weekly trends, spreads, positional S/R |
| **SentimentScout** | 15% | FII/DII flows, global cues, USD/INR, crude, news |
| **RiskManager** | 20% | Position sizing, margin, exposure, daily limits |

## Capital Allocation

- **Total Capital:** ₹1,00,000 (configurable)
- **Intraday:** 40% (₹40,000) - Leverage: 4x
- **Swing:** 60% (₹60,000) - Leverage: 2x

## Decision Rules

1. Each specialist returns a confidence score (0-100) and signal (BUY/SELL/HOLD)
2. Main agent calculates **weighted composite probability**
3. Trade executes only if composite **≥ 70%**
4. Risk manager can BLOCK trades violating limits

## Risk Limits

| Parameter | Value |
|-----------|-------|
| Max loss per trade | ₹2,000 |
| Max daily loss | ₹10,000 |
| Max daily trades | 10 |
| Cooling period | 15 minutes |
| Max position size | ₹1,00,000 |

## Installation

```bash
git clone https://github.com/RahulPali78/tradebot.git
cd tradebot
pip install -r requirements.txt
```

## Usage

### Analyze a Single Symbol
```bash
python main_agent.py --symbol NIFTY
python main_agent.py --symbol BANKNIFTY --swing
```

### Scan Multiple Symbols
```bash
python main_agent.py --scan
```

### Programmatic Usage
```python
from main_agent import TradingOrchestrator

orchestrator = TradingOrchestrator()
result = orchestrator.analyze_symbol("NIFTY", trade_type="INTRADAY")

if result['decision']['confidence'] >= 70:
    print(f"EXECUTE: {result['decision']['signal']}")
```

## Configuration

Edit `config.yaml` to customize:
- Capital allocation
- Decision threshold
- Agent weights
- Risk limits
- Trading hours

## Data Sources

The system uses stub data by default. For live trading:

1. Install `nsepy`: `pip install nsepy`
2. Update `data_sources/nse_data.py` to use real NSE APIs
3. Add broker API integration for order execution

## Project Structure

```
nse-options-agents/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Base agent class
│   ├── options_chain_analyzer.py
│   ├── intraday_strategy_agent.py
│   ├── swing_strategy_agent.py
│   ├── sentiment_scout.py
│   ├── risk_manager.py
│   └── main_decision_agent.py
├── data_sources/
│   └── nse_data.py             # NSE data fetchers (stubbed)
├── utils/                      # Helper utilities
├── memory/                     # Decision history
├── config.yaml                 # System configuration
├── main_agent.py              # Orchestrator
├── requirements.txt
└── README.md
```

## License

MIT

## Disclaimer

This is for educational purposes only. Not financial advice. Trading options involves significant risk.
