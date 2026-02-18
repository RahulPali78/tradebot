"""Main Decision Agent.

Aggregates signals from all specialist agents, calculates weighted confidence,
and makes final trade decision with 70%+ probability threshold.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml
try:
    from agents.base_agent import BaseAgent, AgentResponse
except ImportError:
    from .base_agent import BaseAgent, AgentResponse


class MainDecisionAgent(BaseAgent):
    """Orchestrates all agents and makes final trading decisions."""
    
    def __init__(self, config_path: str = "config.yaml"):
        super().__init__(name="MainDecisionAgent", trade_type="BOTH")
        self.description = "Aggregates agent votes, calculates composite probability, executes if >70%"
        self.agent_weights = self._load_weights(config_path)
        self.threshold = 0.70
        self.decision_history = []
    
    def _load_weights(self, config_path: str) -> Dict[str, float]:
        """Load agent weights from config."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('agent_weights', {
                    'OptionsChainAnalyzer': 0.25,
                    'IntradayStrategyAgent': 0.20,
                    'SwingStrategyAgent': 0.20,
                    'SentimentScout': 0.15,
                    'RiskManager': 0.20
                })
        except Exception:
            return {
                'OptionsChainAnalyzer': 0.25,
                'IntradayStrategyAgent': 0.20,
                'SwingStrategyAgent': 0.20,
                'SentimentScout': 0.15,
                'RiskManager': 0.20
            }
    
    def aggregate(self, agent_responses: List[AgentResponse], 
                  trade_type: str = "INTRADAY") -> AgentResponse:
        """Aggregate all agent responses and make final decision.
        
        Args:
            agent_responses: List of responses from specialist agents
            trade_type: 'INTRADAY' or 'SWING'
            
        Returns:
            Final decision with composite confidence score
        """
        if not agent_responses:
            return AgentResponse(
                agent_name=self.name,
                confidence=0,
                signal="NO_SIGNAL",
                reasoning="No agent responses received",
                metadata={},
                timestamp=datetime.now(),
                trade_type=trade_type
            )
        
        # Track individual agent scores
        buy_agents = []
        sell_agents = []
        hold_agents = []
        total_weighted_score = 0
        total_weight = 0
        
        for response in agent_responses:
            weight = self.agent_weights.get(response.agent_name, 0.1)
            normalized_score = response.confidence / 100.0  # Convert 0-100 to 0-1
            
            # Apply signal direction
            if response.signal in ["BUY", "APPROVE"]:
                weighted_score = normalized_score * weight
                buy_agents.append((response.agent_name, response.confidence, response.reasoning))
            elif response.signal in ["SELL", "BLOCK"]:
                weighted_score = -normalized_score * weight
                sell_agents.append((response.agent_name, response.confidence, response.reasoning))
            else:
                weighted_score = 0
                hold_agents.append((response.agent_name, response.confidence, response.reasoning))
            
            total_weighted_score += weighted_score
            total_weight += weight
        
        # Calculate composite probability (normalized -1 to 1 → 0 to 1)
        if total_weight > 0:
            composite_score = total_weighted_score / total_weight
            composite_probability = (composite_score + 1) / 2  # Map to 0-1
        else:
            composite_probability = 0.5
        
        # Convert to percentage
        final_confidence = composite_probability * 100
        
        # Determine signal based on threshold
        if final_confidence >= 70 and composite_score > 0:
            final_signal = "BUY"
        elif final_confidence >= 70 and composite_score < 0:
            final_signal = "SELL"
        elif final_confidence >= 50:
            final_signal = "HOLD"
        else:
            final_signal = "NO_SIGNAL"
        
        # Build comprehensive reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Composite probability: {final_confidence:.1f}%")
        
        if buy_agents:
            reasoning_parts.append(f"Bullish agents: {', '.join([a[0] for a in buy_agents])}")
        if sell_agents:
            reasoning_parts.append(f"Bearish agents: {', '.join([a[0] for a in sell_agents])}")
        
        # Key insights from individual agents
        for name, conf, reason in buy_agents + sell_agents:
            if conf > 70:
                reasoning_parts.append(f"{name}: {reason[:50]}...")
        
        # Threshold decision
        if final_signal == "NO_SIGNAL":
            reasoning_parts.append(f"Below threshold ({self.threshold*100:.0f}%) - no trade")
        elif final_signal in ["BUY", "SELL"]:
            reasoning_parts.append(f"Above threshold - EXECUTE {final_signal}")
        
        reasoning = " | ".join(reasoning_parts)
        
        # Collect metadata
        metadata = {
            'composite_probability': composite_probability,
            'composite_score': composite_score,
            'buy_agents': len(buy_agents),
            'sell_agents': len(sell_agents),
            'hold_agents': len(hold_agents),
            'agent_details': [r.to_dict() for r in agent_responses],
            'threshold': self.threshold,
            'threshold_met': final_confidence >= 70
        }
        
        decision = AgentResponse(
            agent_name=self.name,
            confidence=final_confidence,
            signal=final_signal,
            reasoning=reasoning,
            metadata=metadata,
            timestamp=datetime.now(),
            trade_type=trade_type
        )
        
        # Store in history
        self.decision_history.append(decision.to_dict())
        
        return decision
    
    def should_execute(self, decision: AgentResponse) -> bool:
        """Check if decision meets execution threshold."""
        return decision.confidence >= 70 and decision.signal in ["BUY", "SELL"]
    
    def analyze(self, symbol: str, **kwargs) -> AgentResponse:
        """Required by BaseAgent - not used directly for MainDecisionAgent."""
        return self.aggregate(kwargs.get('agent_responses', []))
    
    def get_decision_stats(self) -> Dict:
        """Get statistics on past decisions."""
        if not self.decision_history:
            return {}
        
        total = len(self.decision_history)
        above_threshold = sum(1 for d in self.decision_history if d['metadata']['threshold_met'])
        
        return {
            'total_decisions': total,
            'above_threshold': above_threshold,
            'threshold_hit_rate': above_threshold / total if total > 0 else 0,
            'avg_confidence': sum(d['confidence'] for d in self.decision_history) / total
        }
