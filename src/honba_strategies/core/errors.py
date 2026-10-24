"""Structured exception hierarchy for honba-strategies SDK."""

from typing import Any


class HonbaStrategyError(Exception):
    """Base exception for all honba-strategies errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | {self.details}"
        return self.message


class ConfigValidationError(HonbaStrategyError):
    """Raised when strategy configuration validation fails."""

    def __init__(self, field: str, value: Any, constraint: str, details: dict | None = None) -> None:
        msg = f"Config validation failed for '{field}': {value} does not satisfy '{constraint}'"
        super().__init__(msg, details or {"field": field, "value": value, "constraint": constraint})
        self.field = field
        self.value = value
        self.constraint = constraint


class RiskLimitExceededError(HonbaStrategyError):
    """Raised when a risk limit is exceeded."""

    def __init__(self, limit_type: str, current: Any, limit: Any, details: dict | None = None) -> None:
        msg = f"Risk limit exceeded: {limit_type} = {current}, limit = {limit}"
        super().__init__(msg, details or {"limit_type": limit_type, "current": current, "limit": limit})
        self.limit_type = limit_type
        self.current = current
        self.limit = limit


class RegimeNotSupportedError(HonbaStrategyError):
    """Raised when strategy cannot operate in current market regime."""

    def __init__(self, regime: str, strategy: str, details: dict | None = None) -> None:
        msg = f"Strategy '{strategy}' does not support regime: {regime}"
        super().__init__(msg, details or {"regime": regime, "strategy": strategy})
        self.regime = regime
        self.strategy = strategy


class ExecutionError(HonbaStrategyError):
    """Raised when order execution fails."""

    def __init__(self, reason: str, order_id: str | None = None, details: dict | None = None) -> None:
        msg = f"Execution failed: {reason}"
        if order_id:
            msg += f" (order: {order_id})"
        super().__init__(msg, details or {"reason": reason, "order_id": order_id})
        self.reason = reason
        self.order_id = order_id


class DataError(HonbaStrategyError):
    """Raised when required market data is unavailable or malformed."""

    def __init__(self, message: str, instrument: str | None = None, details: dict | None = None) -> None:
        msg = message
        if instrument:
            msg += f" (instrument: {instrument})"
        super().__init__(msg, details or {"instrument": instrument})
        self.instrument = instrument


class InsufficientLiquidityError(ExecutionError):
    """Raised when there is insufficient liquidity to execute an order."""
    pass


class FreezeLimitExceededError(RiskLimitExceededError):
    """Raised when SEBI single-order freeze limit is exceeded."""

    def __init__(self, requested: Any, limit: Any, instrument: str | None = None) -> None:
        super().__init__("freeze_limit", requested, limit,
                         {"instrument": instrument} if instrument else None)
        self.instrument = instrument


class OtrBreachedError(RiskLimitExceededError):
    """Raised when Order-to-Trade Ratio threshold is breached."""

    def __init__(self, current_ratio: float, limit: float, algo_id: str | None = None) -> None:
        super().__init__("otr", current_ratio, limit,
                         {"algo_id": algo_id} if algo_id else None)
        self.algo_id = algo_id


class CircuitBandBreachedError(RiskLimitExceededError):
    """Raised when price moves outside SEBI circuit bands."""

    def __init__(self, price: Any, band_limit: Any, direction: str, instrument: str | None = None) -> None:
        super().__init__("circuit_band", price, band_limit,
                         {"direction": direction, "instrument": instrument} if instrument else None)
        self.direction = direction  # "upper" or "lower"
        self.instrument = instrument


class MisSquareOffError(RiskLimitExceededError):
    """Raised when MIS intraday position must be squared off."""

    def __init__(self, instrument: str, time: str) -> None:
        super().__init__("mis_squareoff", time, "15:20:00 IST",
                         {"instrument": instrument})
        self.instrument = instrument
        self.square_off_time = time


class ConfigurationError(HonbaStrategyError):
    """Raised when SDK or strategy is misconfigured."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        super().__init__(message, {"config_key": config_key} if config_key else None)
        self.config_key = config_key


class StrategyNotFoundError(HonbaStrategyError):
    """Raised when a strategy name is not found in the registry."""

    def __init__(self, name: str, available: list[str] | None = None) -> None:
        msg = f"Strategy not found: {name}"
        if available:
            msg += f". Available: {', '.join(available)}"
        super().__init__(msg, {"name": name, "available": available})
        self.name = name