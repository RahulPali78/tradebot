"""SQLite database for trade history."""
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class TradeHistory:
    """SQLite trade history database."""
    
    def __init__(self, db_file: str = "trades.db"):
        """Initialize database.
        
        Args:
            db_file: Path to SQLite database
        """
        self.db_file = Path(db_file)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity INTEGER NOT NULL,
                    pnl REAL,
                    confidence REAL NOT NULL,
                    strategy TEXT,
                    status TEXT DEFAULT 'OPEN',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL,
                    pnl REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def log_trade(self, trade_data: Dict[str, Any]) -> int:
        """Log a trade.
        
        Args:
            trade_data: Trade data dictionary
            
        Returns:
            Trade ID
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                INSERT INTO trades
                (timestamp, symbol, signal, entry_price, exit_price, quantity, pnl, confidence, strategy, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('timestamp', datetime.now().isoformat()),
                trade_data['symbol'],
                trade_data['signal'],
                trade_data['entry_price'],
                trade_data.get('exit_price'),
                trade_data['quantity'],
                trade_data.get('pnl'),
                trade_data['confidence'],
                trade_data.get('strategy', 'UNKNOWN'),
                trade_data.get('status', 'OPEN')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trades with filtering."""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def close_trade(self, trade_id: int, exit_price: float, pnl: float) -> bool:
        """Close a trade."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                UPDATE trades SET exit_price = ?, pnl = ?, status = 'CLOSED'
                WHERE id = ?
            ''', (exit_price, pnl, trade_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trade statistics."""
        with sqlite3.connect(self.db_file) as conn:
            # Total trades
            total = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
            
            # Win rate
            wins = conn.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0").fetchone()[0]
            losses = conn.execute("SELECT COUNT(*) FROM trades WHERE pnl < 0").fetchone()[0]
            
            # Total P&L
            total_pnl = conn.execute("SELECT COALESCE(SUM(pnl), 0) FROM trades").fetchone()[0]
            
            return {
                'total_trades': total,
                'wins': wins,
                'losses': losses,
                'win_rate': wins / total if total > 0 else 0,
                'total_pnl': total_pnl
            }
