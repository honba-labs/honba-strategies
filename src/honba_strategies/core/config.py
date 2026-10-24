"""Strategy configuration base classes with validation and serialization."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field, fields
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional, get_type_hints

import tomli
import tomli_w
from honba.entities.instrument import InstrumentId


class HonbaStrategyError(Exception):
    """Base exception for honba-strategies SDK."""
    pass


class ConfigValidationError(HonbaStrategyError):
    """Raised when strategy configuration validation fails."""
    pass


class RiskLimitExceededError(HonbaStrategyError):
    """Raised when a risk limit (OTR, drawdown, freeze, circuit) is exceeded."""
    pass


class RegimeNotSupportedError(HonbaStrategyError):
    """Raised when a strategy cannot operate in the current market regime."""
    pass


class ExecutionError(HonbaStrategyError):
    """Raised when order execution fails (rejection, timeout, partial fill)."""
    pass


class DataError(HonbaStrategyError):
    """Raised when required market data is unavailable or malformed."""
    pass


@dataclass
class BaseStrategyConfig(ABC):
    """Base configuration for all strategies.

    Subclasses must define their parameters as dataclass fields with
    type annotations. Validation is performed in __post_init__.
    """

    # Strategy identification
    name: str
    symbol: str
    exchange: str = "NSE"

    # Capital management
    capital: Decimal = Decimal("1000000")
    max_allocation: Decimal = Decimal("1.0")

    # Risk guards
    max_position_pct: Decimal = Decimal("0.10")
    stop_loss_pct: Decimal | None = None
    max_daily_loss_pct: Decimal | None = None

    # Execution defaults
    order_type: str = "MARKET"
    time_in_force: str = "DAY"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.capital <= 0:
            raise ConfigValidationError("capital must be positive")
        if not (Decimal("0") < self.max_allocation <= Decimal("1")):
            raise ConfigValidationError("max_allocation must be in (0, 1]")
        if not (Decimal("0") < self.max_position_pct <= Decimal("1")):
            raise ConfigValidationError("max_position_pct must be in (0, 1]")
        # Ensure instrument_id is available
        if not hasattr(self, "instrument_id"):
            self.instrument_id = InstrumentId(self.symbol, self.exchange)

    @classmethod
    def from_toml(cls: type[BaseStrategyConfig], path: Path) -> BaseStrategyConfig:
        """Load configuration from TOML file."""
        with path.open("rb") as f:
            data = tomli.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls: type[BaseStrategyConfig], data: dict[str, Any]) -> BaseStrategyConfig:
        """Create configuration from dictionary."""
        # Extract nested params if present
        params = data.get("params", {})
        # Flatten top-level and params
        flat = {k: v for k, v in data.items() if k != "params"}
        flat.update(params)

        # Convert string numbers to Decimal
        converted = {}
        for k, v in flat.items():
            if isinstance(v, str) and k in cls._decimal_fields():
                try:
                    converted[k] = Decimal(v)
                except Exception:
                    converted[k] = v
            elif isinstance(v, (int, float)) and k in cls._decimal_fields():
                converted[k] = Decimal(str(v))
            else:
                converted[k] = v

        return cls(**converted)

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to dictionary."""
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, (Decimal, InstrumentId)):
                result[f.name] = str(value)
            else:
                result[f.name] = value
        return result

    def to_toml(self, path: Path) -> None:
        """Write configuration to TOML file."""
        data = self.to_dict()
        with path.open("wb") as f:
            tomli_w.dump(data, f)

    @classmethod
    def _decimal_fields(cls) -> set[str]:
        """Return set of field names that should be Decimal."""
        hints = get_type_hints(cls)
        return {name for name, hint in hints.items() if hint is Decimal or
                (hasattr(hint, "__origin__") and hint.__origin__ is Optional and
                 any(arg is Decimal for arg in hint.__args__))}


@dataclass
class StrategyConfig(BaseStrategyConfig):
    """Extended strategy configuration with dynamic parameter support.

    This class maintains backward compatibility with the catalog's
    config.toml format while adding validation.
    """

    # Dynamic parameters storage
    _params: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        # Ensure instrument_id is available
        if not hasattr(self, "instrument_id"):
            self.instrument_id = InstrumentId(self.symbol, self.exchange)

    @property
    def params(self) -> dict[str, Any]:
        """Get all parameters as a flat dictionary."""
        result = self.to_dict()
        result.update(self._params)
        return result

    def update(self, params: dict[str, Any]) -> None:
        """Update dynamic parameters."""
        for k, v in params.items():
            if isinstance(v, str) and k in self._decimal_fields():
                try:
                    self._params[k] = Decimal(v)
                except Exception:
                    self._params[k] = v
            elif isinstance(v, (int, float)) and k in self._decimal_fields():
                self._params[k] = Decimal(str(v))
            else:
                self._params[k] = v

    def get(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with optional default."""
        return self._params.get(key, getattr(self, key, default))

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._params[key] = value