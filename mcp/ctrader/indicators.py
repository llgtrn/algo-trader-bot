"""Minimal technical-indicator library for the cTrader bot.

`ctrader_bot.get_indicator_data` imports `TechnicalIndicators` from here. The
upstream repo shipped without this module, so `get_indicator` was dead. This is
a dependency-light implementation (pandas + numpy only) covering the indicators
the bot references.

Conventions:
- Single-series indicators return a pandas ``Series`` aligned to the input index.
- Multi-output indicators (macd, bollinger, stochastic) return a pandas
  ``DataFrame`` so the MCP server can serialize them uniformly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Stateless indicator calculations over pandas price columns."""

    # ----------------------------------------------------------- moving averages
    @staticmethod
    def sma(close: pd.Series, period: int = 14) -> pd.Series:
        return close.rolling(window=period, min_periods=period).mean()

    @staticmethod
    def ema(close: pd.Series, period: int = 14) -> pd.Series:
        return close.ewm(span=period, adjust=False).mean()

    # --------------------------------------------------------------------- macd
    @staticmethod
    def macd(
        close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        ema_fast = TechnicalIndicators.ema(close, fast)
        ema_slow = TechnicalIndicators.ema(close, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame(
            {
                "macd": macd_line,
                "signal": signal_line,
                "histogram": macd_line - signal_line,
            }
        )

    # ---------------------------------------------------------------------- rsi
    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        # Wilder's smoothing.
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    # ---------------------------------------------------------- bollinger bands
    @staticmethod
    def bollinger_bands(
        close: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> pd.DataFrame:
        middle = TechnicalIndicators.sma(close, period)
        std = close.rolling(window=period, min_periods=period).std()
        return pd.DataFrame(
            {
                "upper": middle + std_dev * std,
                "middle": middle,
                "lower": middle - std_dev * std,
            }
        )

    # ---------------------------------------------------------------------- cci
    @staticmethod
    def cci(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20
    ) -> pd.Series:
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=period, min_periods=period).mean()
        mad = tp.rolling(window=period, min_periods=period).apply(
            lambda x: np.abs(x - x.mean()).mean(), raw=True
        )
        return (tp - sma_tp) / (0.015 * mad)

    # -------------------------------------------------------------- true range
    @staticmethod
    def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        prev_close = close.shift(1)
        ranges = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
        )
        return ranges.max(axis=1)

    @staticmethod
    def atr(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        tr = TechnicalIndicators._true_range(high, low, close)
        return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # -------------------------------------------------------- chaikin volatility
    @staticmethod
    def chaikin_volatility(
        high: pd.Series,
        low: pd.Series,
        ema_period: int = 10,
        change_period: int = 10,
    ) -> pd.Series:
        hl_ema = (high - low).ewm(span=ema_period, adjust=False).mean()
        return (hl_ema - hl_ema.shift(change_period)) / hl_ema.shift(change_period) * 100

    # -------------------------------------------------------------- stochastic
    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> pd.DataFrame:
        lowest = low.rolling(window=k_period, min_periods=k_period).min()
        highest = high.rolling(window=k_period, min_periods=k_period).max()
        k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
        d = k.rolling(window=d_period, min_periods=d_period).mean()
        return pd.DataFrame({"k": k, "d": d})

    # ---------------------------------------------------------------------- adx
    @staticmethod
    def adx(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        tr = TechnicalIndicators._true_range(high, low, close)
        atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(
            alpha=1 / period, adjust=False
        ).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(
            alpha=1 / period, adjust=False
        ).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        return dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # ---------------------------------------------------------------------- obv
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        direction = np.sign(close.diff()).fillna(0)
        return (direction * volume).cumsum()

    # --------------------------------------------------------------------- vwap
    @staticmethod
    def vwap(
        high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
    ) -> pd.Series:
        tp = (high + low + close) / 3
        cum_vol = volume.cumsum().replace(0, np.nan)
        return (tp * volume).cumsum() / cum_vol
