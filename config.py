"""Configuration management using Pydantic settings."""

from typing import List, Optional
from datetime import time
from pathlib import Path
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CapitalAllocationConfig(BaseSettings):
    """Capital allocation settings."""
    total_capital: int = Field(default=100000, ge=10000, le=100000000)
    intraday_allocation_pct: int = Field(default=40, ge=10, le=90)
    swing_allocation_pct: int = Field(default=60, ge=10, le=90)

    @field_validator('intraday_allocation_pct', 'swing_allocation_pct')
    @classmethod
    def validate_allocation(cls, v, info):
        """Ensure allocations don't exceed 100%."""
        return v


class DecisionConfig(BaseSettings):
    """Decision thresholds."""
    min_probability_threshold: float = Field(default=0.70, ge=0.50, le=0.99)
    max_daily_trades: int = Field(default=10, ge=1, le=100)
    cooling_period_minutes: int = Field(default=15, ge=0, le=60)


class RiskManagementConfig(BaseSettings):
    """Risk management settings."""
    max_loss_per_trade: int = Field(default=2000, ge=500, le=50000)
    max_daily_loss: int = Field(default=10000, ge=1000, le=200000)
    max_position_size: int = Field(default=100000, ge=10000, le=10000000)
    intraday_leverage: int = Field(default=4, ge=1, le=10)
    swing_leverage: int = Field(default=2, ge=1, le=5)


class AgentWeightsConfig(BaseSettings):
    """Agent weights for weighted probability calculation."""
    OptionsChainAnalyzer: float = Field(default=0.25, ge=0.0, le=1.0)
    IntradayStrategyAgent: float = Field(default=0.20, ge=0.0, le=1.0)
    SwingStrategyAgent: float = Field(default=0.20, ge=0.0, le=1.0)
    SentimentScout: float = Field(default=0.15, ge=0.0, le=1.0)
    RiskManager: float = Field(default=0.20, ge=0.0, le=1.0)

    @field_validator('*')
    @classmethod
    def validate_weights(cls, v):
        """Ensure all weights are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Weight must be between 0 and 1')
        return v

    @computed_field
    @property
    def sum_weights(self) -> float:
        """Return sum of all weights."""
        return sum([
            self.OptionsChainAnalyzer,
            self.IntradayStrategyAgent,
            self.SwingStrategyAgent,
            self.SentimentScout,
            self.RiskManager
        ])


class TradingHoursConfig(BaseSettings):
    """Trading hours configuration."""
    market_open: str = "09:15"
    market_close: str = "15:30"
    pre_market: str = "09:00"
    intraday_cutoff: str = "14:30"


class DataSourcesConfig(BaseSettings):
    """Data source configuration."""
    use_nsepy: bool = True
    use_yahoo_finance: bool = True
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)


class NotificationsConfig(BaseSettings):
    """Notification settings."""
    enabled: bool = True
    channels: List[str] = ["console"]
    min_trade_size_for_notification: int = Field(default=10000, ge=1000, le=1000000)


class AlertConfig(BaseSettings):
    """Alert/notification settings."""
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_from: str = Field(default="TradeBot <tradebot@example.com>")
    alert_emails: List[str] = Field(default_factory=list)
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)

    @computed_field
    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.smtp_user and self.smtp_password)


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    log_level: str = Field(default="INFO")
    log_file_path: Path = Field(default=Path("logs/tradebot.log"))
    log_max_bytes: int = Field(default=10_485_760, ge=1_048_576, le=104_857_600)
    log_backup_count: int = Field(default=5, ge=1, le=50)


class APIKeys(BaseSettings):
    """API Keys configuration."""
    nse_api_key: Optional[str] = Field(default=None, alias="NSE_API_KEY")
    nse_api_secret: Optional[str] = Field(default=None, alias="NSE_API_SECRET")
    zerodha_api_key: Optional[str] = Field(default=None, alias="ZERODHA_API_KEY")
    zerodha_api_secret: Optional[str] = Field(default=None, alias="ZERODHA_API_SECRET")
    zerodha_access_token: Optional[str] = Field(default=None, alias="ZERODHA_ACCESS_TOKEN")
    alice_blue_api_key: Optional[str] = Field(default=None, alias="ALICE_BLUE_API_KEY")
    alpha_vantage_api_key: Optional[str] = Field(default=None, alias="ALPHA_VANTAGE_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class TradeSettings(BaseSettings):
    """Core trading settings."""
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    dry_run: bool = Field(default=True)  # Run in simulation mode by default


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False)
    dry_run: bool = Field(default=True, description="Run in simulation mode without actual trades")
    
    # Sub-configs
    capital: CapitalAllocationConfig = Field(default_factory=CapitalAllocationConfig)
    decision: DecisionConfig = Field(default_factory=DecisionConfig)
    risk: RiskManagementConfig = Field(default_factory=RiskManagementConfig)
    agent_weights: AgentWeightsConfig = Field(default_factory=AgentWeightsConfig)
    trading_hours: TradingHoursConfig = Field(default_factory=TradingHoursConfig)
    data_sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    api_keys: APIKeys = Field(default_factory=APIKeys)
    trading: TradeSettings = Field(default_factory=TradeSettings)
    
    # Database
    database_url: str = Field(default="sqlite:///data/tradebot.db", alias="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @computed_field
    @property
    def log_file_path(self) -> Path:
        """Ensure log directory exists."""
        path = Path(self.logging.log_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator('env')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ['development', 'staging', 'production', 'test']
        if v.lower() not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v.lower()


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
