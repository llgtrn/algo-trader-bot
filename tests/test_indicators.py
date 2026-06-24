import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parent.parent / "mcp" / "ctrader"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from indicators import TechnicalIndicators as TI  # noqa: E402


@pytest.fixture
def ohlcv():
    n = 120
    rng = np.linspace(1.10, 1.15, n) + 0.002 * np.sin(np.arange(n))
    close = pd.Series(rng)
    high = close + 0.001
    low = close - 0.001
    volume = pd.Series(np.full(n, 1000.0))
    return high, low, close, volume


def test_sma_ema_shapes(ohlcv):
    _, _, close, _ = ohlcv
    assert len(TI.sma(close, 14)) == len(close)
    assert len(TI.ema(close, 14)) == len(close)
    # EMA has no NaN warmup; SMA does for the first period-1 points.
    assert TI.ema(close, 14).notna().all()
    assert TI.sma(close, 14).isna().sum() == 13


def test_rsi_bounds(ohlcv):
    _, _, close, _ = ohlcv
    rsi = TI.rsi(close, 14).dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()


def test_macd_columns(ohlcv):
    _, _, close, _ = ohlcv
    macd = TI.macd(close)
    assert list(macd.columns) == ["macd", "signal", "histogram"]
    # histogram = macd - signal
    np.testing.assert_allclose(
        (macd["macd"] - macd["signal"]).values, macd["histogram"].values, atol=1e-12
    )


def test_bollinger_ordering(ohlcv):
    _, _, close, _ = ohlcv
    bb = TI.bollinger_bands(close, 20, 2.0).dropna()
    assert (bb["upper"] >= bb["middle"]).all()
    assert (bb["middle"] >= bb["lower"]).all()


def test_atr_positive(ohlcv):
    high, low, close, _ = ohlcv
    atr = TI.atr(high, low, close, 14).dropna()
    assert (atr > 0).all()


def test_stochastic_columns_bounded(ohlcv):
    high, low, close, _ = ohlcv
    st = TI.stochastic(high, low, close, 14, 3).dropna()
    assert list(st.columns) == ["k", "d"]
    assert ((st["k"] >= 0) & (st["k"] <= 100)).all()


def test_obv_vwap_run(ohlcv):
    high, low, close, volume = ohlcv
    assert len(TI.obv(close, volume)) == len(close)
    vwap = TI.vwap(high, low, close, volume)
    assert vwap.notna().sum() > 0


def test_adx_cci_run(ohlcv):
    high, low, close, _ = ohlcv
    assert len(TI.adx(high, low, close, 14)) == len(close)
    assert len(TI.cci(high, low, close, 20)) == len(close)
