# API Reference - cTrader MCP Server

Complete reference for all 14 tools available in the cTrader MCP Server.

## Tool Categories

- [Account Management](#account-management) (4 tools)
- [Trading Operations](#trading-operations) (5 tools)
- [Market Data & Analysis](#market-data--analysis) (5 tools)

---

## Account Management

### get_account_status

Get comprehensive account information including balance, equity, margin, and P&L.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "account_status": {
    "account_id": 12345,
    "balance": 10000.00,
    "equity": 10250.50,
    "margin": 500.00,
    "free_margin": 9750.50,
    "positions_count": 2,
    "orders_count": 1,
    "total_pnl": 250.50,
    "total_swap": -2.50,
    "total_commission": -1.70,
    "net_pnl": 246.30
  }
}
```

**Example Usage:**
```
AI Assistant: "Let me check your account status..."
[Calls get_account_status]
AI Assistant: "Your account has $10,000 balance with $10,250 equity. 
              You have 2 open positions with a net P&L of +$246.30."
```

---

### get_positions

List all open positions with detailed information.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "count": 2,
  "positions": [
    {
      "position_id": 123456,
      "symbol": "EURUSD",
      "side": "BUY",
      "volume": 0.01,
      "entry_price": 1.09000,
      "pnl": 15.50,
      "swap": -0.25,
      "commission": -0.50
    },
    {
      "position_id": 123457,
      "symbol": "GBPUSD",
      "side": "SELL",
      "volume": 0.02,
      "entry_price": 1.26500,
      "pnl": -8.30,
      "swap": -0.30,
      "commission": -1.00
    }
  ]
}
```

---

### get_pending_orders

Get all pending limit and stop orders.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "count": 1,
  "orders": [
    {
      "order_id": 789012,
      "symbol": "EURUSD",
      "side": "BUY",
      "volume": 0.01
    }
  ]
}
```

---

### get_position_pnl

Get detailed profit/loss information for one or all positions.

**Parameters:**
- `position_id` (integer, optional): Specific position ID. Returns all if omitted.

**Returns (single position):**
```json
{
  "success": true,
  "position_id": 123456,
  "data": {
    "pnl": 15.50,
    "swap": -0.25,
    "commission": -0.50
  }
}
```

**Returns (all positions):**
```json
{
  "success": true,
  "position_id": null,
  "data": [
    {
      "id": 123456,
      "symbol": "EURUSD",
      "side": "BUY",
      "volume": 0.01,
      "pnl": 15.50,
      "swap": -0.25,
      "commission": -0.50
    }
  ]
}
```

---

## Trading Operations

### create_market_order

Create a market order that executes immediately at the current market price.

**Parameters:**
- `symbol` (string, required): Symbol name (e.g., "EURUSD", "BTCUSD")
- `side` (string, required): "BUY" or "SELL"
- `volume` (number, required): Volume in lots (e.g., 0.01)
- `stop_loss` (number, optional): Stop loss price
- `take_profit` (number, optional): Take profit price

**Example:**
```json
{
  "symbol": "EURUSD",
  "side": "BUY",
  "volume": 0.01,
  "stop_loss": 1.08000,
  "take_profit": 1.10000
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Market order created",
  "order_details": {
    "symbol": "EURUSD",
    "side": "BUY",
    "volume": 0.01,
    "stop_loss": 1.08000,
    "take_profit": 1.10000
  }
}
```

---

### create_limit_order

Create a limit order that executes when price reaches a specified level.

**Parameters:**
- `symbol` (string, required): Symbol name
- `side` (string, required): "BUY" or "SELL"
- `volume` (number, required): Volume in lots
- `price` (number, required): Limit price
- `stop_loss` (number, optional): Stop loss price
- `take_profit` (number, optional): Take profit price

**Example:**
```json
{
  "symbol": "EURUSD",
  "side": "BUY",
  "volume": 0.01,
  "price": 1.09000,
  "stop_loss": 1.08000,
  "take_profit": 1.10000
}
```

---

### create_stop_order

Create a stop order that triggers when price reaches a specified level.

**Parameters:**
- `symbol` (string, required): Symbol name
- `side` (string, required): "BUY" or "SELL"
- `volume` (number, required): Volume in lots
- `price` (number, required): Stop trigger price
- `stop_loss` (number, optional): Stop loss price
- `take_profit` (number, optional): Take profit price

**Example:**
```json
{
  "symbol": "EURUSD",
  "side": "SELL",
  "volume": 0.01,
  "price": 1.08500,
  "stop_loss": 1.09000,
  "take_profit": 1.08000
}
```

---

### close_position

Close an open position fully or partially.

**Parameters:**
- `position_id` (integer, required): Position ID to close
- `volume` (number, optional): Volume to close in lots. If omitted, closes entire position.

**Example (full close):**
```json
{
  "position_id": 123456
}
```

**Example (partial close):**
```json
{
  "position_id": 123456,
  "volume": 0.005
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Position closed",
  "position_id": 123456,
  "volume": 0.01
}
```

---

### cancel_order

Cancel a pending order.

**Parameters:**
- `order_id` (integer, required): Order ID to cancel

**Example:**
```json
{
  "order_id": 789012
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Order cancelled",
  "order_id": 789012
}
```

---

## Market Data & Analysis

### list_symbols

List available trading symbols with optional filtering.

**Parameters:**
- `filter` (string, optional): Filter text (case-insensitive). Default: ""

**Example:**
```json
{
  "filter": "EUR"
}
```

**Returns:**
```json
{
  "success": true,
  "count": 45,
  "symbols": [
    "EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD",
    "EURCAD", "EURNZD", "EURSGD", ...
  ]
}
```

---

### get_historical_data

Get historical OHLCV candlestick data.

**Parameters:**
- `symbol` (string, required): Symbol name
- `timeframe` (string, optional): "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", or "MN1". Default: "H1"
- `count` (integer, optional): Number of candles. Default: 100

**Example:**
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "count": 50
}
```

**Returns:**
```json
{
  "success": true,
  "symbol": "EURUSD",
  "timeframe": "H1",
  "count": 50,
  "data": [
    {
      "timestamp": "2025-10-10T10:00:00",
      "open": 1.09000,
      "high": 1.09100,
      "low": 1.08900,
      "close": 1.09050,
      "volume": 12345
    },
    ...
  ]
}
```

---

### get_indicator

Calculate technical indicators.

**Parameters:**
- `symbol` (string, required): Symbol name
- `indicator` (string, required): "ema", "sma", "rsi", "macd", "bbands", "atr", or "stochastic"
- `timeframe` (string, optional): Timeframe. Default: "H1"
- `period` (integer, optional): Indicator period. Default: 14

**Example (RSI):**
```json
{
  "symbol": "EURUSD",
  "indicator": "rsi",
  "timeframe": "H1",
  "period": 14
}
```

**Example (MACD):**
```json
{
  "symbol": "GBPUSD",
  "indicator": "macd",
  "timeframe": "H1"
}
```

**Returns (RSI):**
```json
{
  "success": true,
  "symbol": "EURUSD",
  "indicator": "rsi",
  "timeframe": "H1",
  "period": 14,
  "data": {
    "current": 65.3,
    "values": [62.1, 63.5, 64.8, 65.3, ...]
  }
}
```

**Supported Indicators:**
- **EMA** - Exponential Moving Average
- **SMA** - Simple Moving Average
- **RSI** - Relative Strength Index
- **MACD** - Moving Average Convergence Divergence
- **BBands** - Bollinger Bands
- **ATR** - Average True Range
- **Stochastic** - Stochastic Oscillator

---

### subscribe_to_ticks

Subscribe to real-time tick data for a symbol.

**Parameters:**
- `symbol` (string, required): Symbol name

**Example:**
```json
{
  "symbol": "EURUSD"
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Subscribed to EURUSD ticks",
  "symbol": "EURUSD"
}
```

**Note:** Tick data will be printed to the bot's output stream.

---

### unsubscribe_from_ticks

Unsubscribe from real-time tick data.

**Parameters:**
- `symbol` (string, required): Symbol name

**Example:**
```json
{
  "symbol": "EURUSD"
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Unsubscribed from EURUSD ticks",
  "symbol": "EURUSD"
}
```

---

## Error Handling

All tools return error information when something goes wrong:

```json
{
  "error": "Error message here",
  "tool": "tool_name",
  "arguments": {...}
}
```

Common errors:
- **"Bot not ready"** - Server is still initializing
- **"Symbol not found"** - Invalid symbol name
- **"Position not found"** - Invalid position ID
- **"Order not found"** - Invalid order ID
- **"Not authenticated"** - Authentication failed

---

## Rate Limits

The cTrader API enforces rate limits:
- **50 requests/second** - Trading operations, account queries
- **5 requests/second** - Historical data requests

The server automatically respects these limits.

---

## Timeframe Reference

| Code | Description |
|------|-------------|
| M1 | 1 Minute |
| M5 | 5 Minutes |
| M15 | 15 Minutes |
| M30 | 30 Minutes |
| H1 | 1 Hour |
| H4 | 4 Hours |
| D1 | 1 Day |
| W1 | 1 Week |
| MN1 | 1 Month |

---

## Volume Units

Volume is specified in **lots**:
- **1.00** = 1 standard lot (100,000 units for forex)
- **0.10** = 1 mini lot (10,000 units)
- **0.01** = 1 micro lot (1,000 units)

Minimum volume varies by broker and symbol.

---

## Best Practices

1. **Always use stop-loss** for risk management
2. **Test on demo account** before live trading
3. **Start with small volumes** (0.01 lots)
4. **Monitor positions regularly**
5. **Keep credentials secure**

---

**For more information, see the [Complete Guide](GUIDE.md)**
