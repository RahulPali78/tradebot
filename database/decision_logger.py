"""JSON-based decision logging."""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class DecisionLogger:
    """Log trading decisions to JSON file."""
    
    def __init__(self, log_file: str = "decisions.json"):
        """Initialize decision logger.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = Path(log_file)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Ensure log file exists."""
        if not self.log_file.exists():
            self.log_file.write_text('[]')
    
    def log_decision(
        self,
        symbol: str,
        decision: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> None:
        """Log a trading decision.
        
        Args:
            symbol: Trading symbol
            decision: Decision dictionary
            timestamp: Optional timestamp (default: now)
        """
        timestamp = timestamp or datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "symbol": symbol,
            **decision
        }
        
        try:
            with open(self.log_file, 'r+') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                
                data.append(entry)
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to log decision: {e}")
    
    def get_decisions(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decisions with optional filtering.
        
        Args:
            symbol: Filter by symbol
            start_date: Filter from date (ISO format)
            end_date: Filter to date (ISO format)
            limit: Maximum number of results
            
        Returns:
            List of decision entries
        """
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
        
        # Apply filters
        if symbol:
            data = [d for d in data if d.get('symbol') == symbol]
        
        if start_date:
            data = [d for d in data if d.get('timestamp', '') >= start_date]
        
        if end_date:
            data = [d for d in data if d.get('timestamp', '') <= end_date]
        
        # Return most recent first, limited
        return sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    def clear(self) -> None:
        """Clear all logged decisions."""
        with open(self.log_file, 'w') as f:
            f.write('[]')
