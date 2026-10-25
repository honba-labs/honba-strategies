"""Reusable Alpha Signal Generators.

Modular signal components that can be composed with position sizers and execution
algorithms to build complete trading systems.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from honba_strategies.components.sizers.base import Signal


class CointegrationSignal:
    """Cointegration Spread Signal for Pairs Trading.

    Computes the cointegration spread between two assets:
        S_t = log(P_A) - beta * log(P_B) - alpha

    Emits signals when z-score crosses entry/exit thresholds.
    """

    def __init__(
        self,
        symbol_a: str,
        symbol_b: str,
        lookback_window: int = 60,
        z_entry: Decimal = Decimal("2.0"),
        z_exit: Decimal = Decimal("0.0"),
        z_stop: Decimal = Decimal("3.5"),
    ) -> None:
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b
        self.lookback_window = lookback_window
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.z_stop = z_stop

        # Rolling statistics
        self._spreads: list[Decimal] = []
        self._hedge_ratio: Decimal | None = None
        self._intercept: Decimal | None = None
        self._spread_mean: Decimal | None = None
        self._spread_std: Decimal | None = None

    def update(self, price_a: Decimal, price_b: Decimal) -> Signal | None:
        """Update with new prices and return signal if threshold crossed."""
        import math

        if price_a <= 0 or price_b <= 0:
            return None

        # Log prices
        log_a = Decimal(str(math.log(float(price_a))))
        log_b = Decimal(str(math.log(float(price_b))))

        # Need enough data to estimate hedge ratio
        if len(self._spreads) < self.lookback_window:
            self._spreads.append(log_a - log_b)  # Temporary spread
            return None

        # Re-estimate hedge ratio periodically (simplified: OLS on log prices)
        if self._hedge_ratio is None or len(self._spreads) % 20 == 0:
            self._estimate_hedge_ratio()

        if self._hedge_ratio is None or self._intercept is None:
            return None

        # Compute current spread
        spread = log_a - self._hedge_ratio * log_b - self._intercept
        self._spreads.append(spread)

        # Keep window
        if len(self._spreads) > self.lookback_window:
            self._spreads.pop(0)

        # Update rolling mean/std
        self._update_spread_stats()

        if self._spread_mean is None or self._spread_std is None or self._spread_std == 0:
            return None

        # Compute z-score
        z_score = (spread - self._spread_mean) / self._spread_std

        # Determine signal
        direction = 0
        stop_loss = None
        entry_price = price_a  # Primary leg price

        if z_score <= -self.z_entry:
            # Spread is cheap: long A, short B
            direction = 1
            stop_loss = price_a * (Decimal("1") - self.z_stop / Decimal("100"))
        elif z_score >= self.z_entry:
            # Spread is rich: short A, long B
            direction = -1
            stop_loss = price_a * (Decimal("1") + self.z_stop / Decimal("100"))
        elif abs(z_score) <= self.z_exit:
            # Exit signal
            direction = 0

        return Signal(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            volatility_atr=None,  # Would need ATR from market data
            confidence=min(Decimal("1"), abs(z_score) / self.z_entry),
            metadata={
                "spread": str(spread),
                "z_score": str(z_score),
                "hedge_ratio": str(self._hedge_ratio) if self._hedge_ratio else None,
                "symbol_a": self.symbol_a,
                "symbol_b": self.symbol_b,
            },
        )

    def _estimate_hedge_ratio(self) -> None:
        """Estimate hedge ratio via OLS on log prices."""
        # Simplified: would use proper OLS in production
        if len(self._spreads) < 2:
            return

        # Use recent spreads to estimate
        # This is a placeholder - real implementation would use log prices of both legs
        self._hedge_ratio = Decimal("1.0")
        self._intercept = Decimal("0.0")

    def _update_spread_stats(self) -> None:
        """Update rolling mean and std of spread."""
        if len(self._spreads) < 2:
            return

        mean = sum(self._spreads) / Decimal(str(len(self._spreads)))
        variance = sum((x - mean) ** 2 for x in self._spreads) / Decimal(str(len(self._spreads)))
        std = variance.sqrt()

        self._spread_mean = mean
        self._spread_std = std


class OrnsteinUhlenbeckSignal:
    """Ornstein-Uhlenbeck Stochastic Process Mean Reversion Signal.

    Fits continuous-time OU process: dX_t = theta * (mu - X_t) * dt + sigma * dW_t

    Trades only scrips with half-life t_1/2 = ln(2)/theta < 5 days.
    """

    def __init__(
        self,
        symbol: str,
        lookback_window: int = 100,
        max_half_life_days: Decimal = Decimal("5"),
        z_entry: Decimal = Decimal("1.5"),
        z_exit: Decimal = Decimal("0.0"),
    ) -> None:
        self.symbol = symbol
        self.lookback_window = lookback_window
        self.max_half_life_days = max_half_life_days
        self.z_entry = z_entry
        self.z_exit = z_exit

        self._prices: list[Decimal] = []
        self._log_prices: list[Decimal] = []
        self._theta: Decimal | None = None
        self._mu: Decimal | None = None
        self._sigma: Decimal | None = None
        self._half_life: Decimal | None = None

    def update(self, price: Decimal) -> Signal | None:
        """Update with new price and return signal if conditions met."""
        import math

        if price <= 0:
            return None

        self._prices.append(price)
        self._log_prices.append(Decimal(str(math.log(float(price)))))

        if len(self._log_prices) > self.lookback_window:
            self._log_prices.pop(0)
            self._prices.pop(0)

        # Need enough data for OU estimation
        if len(self._log_prices) < 20:
            return None

        # Estimate OU parameters
        self._estimate_ou_parameters()

        if self._theta is None or self._mu is None or self._sigma is None:
            return None

        # Check half-life constraint
        if self._half_life is not None and self._half_life > self.max_half_life_days:
            return None  # Don't trade slow mean-reverting assets

        current_log_price = self._log_prices[-1]

        # Expected value at next step: E[X_{t+1}] = mu + (X_t - mu) * exp(-theta * dt)
        # For daily dt=1: exp(-theta)
        # Deviation from equilibrium
        deviation = current_log_price - self._mu

        # Z-score: deviation / (sigma / sqrt(2*theta))
        if self._sigma > 0 and self._theta > 0:
            stationary_std = self._sigma / (Decimal("2") * self._theta).sqrt()
            if stationary_std > 0:
                z_score = deviation / stationary_std
            else:
                return None
        else:
            return None

        # Signal logic
        direction = 0
        stop_loss = None
        entry_price = price

        if z_score <= -self.z_entry:
            # Price below equilibrium: long
            direction = 1
            # Stop at 2x entry z-score
            stop_price_log = self._mu - self.z_entry * Decimal("2") * stationary_std
            stop_loss = Decimal(str(math.exp(float(stop_price_log))))
        elif z_score >= self.z_entry:
            # Price above equilibrium: short
            direction = -1
            stop_price_log = self._mu + self.z_entry * Decimal("2") * stationary_std
            stop_loss = Decimal(str(math.exp(float(stop_price_log))))
        elif abs(z_score) <= self.z_exit:
            direction = 0

        return Signal(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            volatility_atr=self._sigma * price if self._sigma else None,
            confidence=min(Decimal("1"), abs(z_score) / self.z_entry),
            metadata={
                "ou_theta": str(self._theta) if self._theta else None,
                "ou_mu": str(self._mu) if self._mu else None,
                "ou_sigma": str(self._sigma) if self._sigma else None,
                "half_life_days": str(self._half_life) if self._half_life else None,
                "z_score": str(z_score),
                "deviation": str(deviation),
                "symbol": self.symbol,
            },
        )

    def _estimate_ou_parameters(self) -> None:
        """Estimate OU parameters using MLE/discrete approximation."""
        import math

        if len(self._log_prices) < 2:
            return

        # Discrete AR(1) approximation: X_{t+1} = c + phi * X_t + eps
        # where phi = exp(-theta * dt), c = mu * (1 - phi)
        n = len(self._log_prices)
        x = self._log_prices[:-1]
        y = self._log_prices[1:]

        # OLS for AR(1)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n - 1))
        sum_x2 = sum(xi * xi for xi in x)

        denom = Decimal(str(n - 1)) * sum_x2 - sum_x * sum_x
        if denom == 0:
            return

        phi = (Decimal(str(n - 1)) * sum_xy - sum_x * sum_y) / denom
        c = (sum_y - phi * sum_x) / Decimal(str(n - 1))

        # Convert to continuous time (dt=1 day)
        if phi > 0 and phi < 1:
            self._theta = -Decimal(str(math.log(float(phi))))
            if self._theta > 0:
                self._mu = c / (Decimal("1") - phi)
                self._half_life = Decimal(str(math.log(2))) / self._theta

        # Estimate sigma from residuals
        if self._theta is not None and self._mu is not None:
            residuals = []
            for i in range(n - 1):
                pred = c + phi * x[i]
                residuals.append(y[i] - pred)

            if residuals:
                var = sum(r * r for r in residuals) / Decimal(str(len(residuals)))
                # sigma = sqrt(var * 2 * theta / (1 - phi^2))
                if phi * phi < 1:
                    self._sigma = (var * Decimal("2") * self._theta / (Decimal("1") - phi * phi)).sqrt()


class DonchianBreakoutSignal:
    """Donchian Channel Breakout Signal.

    Classic Richard Dennis Turtle-style breakout on N-period high/low channels.
    Emits signal with ATR-based stop-loss.
    """

    def __init__(
        self,
        symbol: str,
        entry_period: int = 20,
        exit_period: int = 10,
        atr_period: int = 20,
        atr_stop_mult: Decimal = Decimal("2.0"),
    ) -> None:
        self.symbol = symbol
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        self.atr_stop_mult = atr_stop_mult

        self._highs: list[Decimal] = []
        self._lows: list[Decimal] = []
        self._closes: list[Decimal] = []
        self._atr: Decimal | None = None

        # Position state
        self._position: int = 0  # +1 long, -1 short, 0 flat
        self._entry_price: Decimal | None = None

    def update(self, high: Decimal, low: Decimal, close: Decimal) -> Signal | None:
        """Update with new bar and return signal if breakout occurs."""
        self._highs.append(high)
        self._lows.append(low)
        self._closes.append(close)

        max_period = max(self.entry_period, self.exit_period, self.atr_period)
        if len(self._highs) > max_period:
            self._highs.pop(0)
            self._lows.pop(0)
            self._closes.pop(0)

        if len(self._closes) < self.atr_period:
            return None

        # Update ATR
        self._update_atr()

        # Calculate channels
        upper_channel = max(self._highs[-self.entry_period:])
        lower_channel = min(self._lows[-self.entry_period:])
        exit_upper = max(self._highs[-self.exit_period:])
        exit_lower = min(self._lows[-self.exit_period:])

        current_price = close
        direction = 0
        stop_loss = None

        if self._position == 0:
            # Check entry breakouts
            if current_price >= upper_channel:
                direction = 1
                self._position = 1
                self._entry_price = current_price
                if self._atr:
                    stop_loss = current_price - self._atr * self.atr_stop_mult
            elif current_price <= lower_channel:
                direction = -1
                self._position = -1
                self._entry_price = current_price
                if self._atr:
                    stop_loss = current_price + self._atr * self.atr_stop_mult
        elif self._position > 0:
            # Check exits for long
            atr_stop = self._atr * self.atr_stop_mult * Decimal("2") if self._atr else None
            if current_price <= exit_lower or (self._entry_price and atr_stop is not None and current_price <= self._entry_price - atr_stop):
                direction = 0  # Exit
                self._position = 0
                self._entry_price = None
        elif self._position < 0:
            # Check exits for short
            atr_stop = self._atr * self.atr_stop_mult * Decimal("2") if self._atr else None
            if current_price >= exit_upper or (self._entry_price and atr_stop is not None and current_price >= self._entry_price + atr_stop):
                direction = 0  # Exit
                self._position = 0
                self._entry_price = None

        if direction == 0 and self._position == 0:
            return None  # No signal

        entry_price = self._entry_price if self._position != 0 else current_price
        # entry_price is guaranteed to be Decimal since current_price is Decimal and self._entry_price is Decimal when position != 0
        assert entry_price is not None

        return Signal(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            volatility_atr=self._atr,
            confidence=Decimal("1") if direction != 0 else Decimal("0"),
            metadata={
                "upper_channel": str(upper_channel),
                "lower_channel": str(lower_channel),
                "exit_upper": str(exit_upper),
                "exit_lower": str(exit_lower),
                "atr": str(self._atr) if self._atr else None,
                "position": self._position,
                "symbol": self.symbol,
            },
        )

    def _update_atr(self) -> None:
        """Update Average True Range."""
        if len(self._closes) < self.atr_period + 1:
            return

        true_ranges = []
        for i in range(-self.atr_period, 0):
            high = self._highs[i]
            low = self._lows[i]
            prev_close = self._closes[i - 1] if i > -self.atr_period else self._closes[0]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        self._atr = sum(true_ranges) / Decimal(str(len(true_ranges)))