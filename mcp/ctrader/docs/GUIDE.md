# cTrader MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to interact with cTrader trading platform.

## Overview

This MCP server provides AI assistants with the ability to:
- Access account status and trading information
- Create market, limit, and stop orders
- Manage positions and pending orders
- Retrieve historical market data
- Calculate technical indicators
- Subscribe to real-time price feeds

## Features

### Trading Operations
- **Market Orders**: Execute trades immediately at current market price
- **Limit Orders**: Place orders that execute when price reaches a specified level
- **Stop Orders**: Place stop-loss or stop-entry orders
- **Position Management**: Close positions fully or partially
- **Order Management**: Cancel pending orders

### Market Data
- **Historical Data**: OHLCV candlestick data across multiple timeframes (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
- **Technical Indicators**: EMA, SMA, RSI, MACD, Bollinger Bands, ATR, Stochastic
- **Real-time Ticks**: Subscribe to live bid/ask price updates

### Account Information
- Balance, equity, margin information
- Open positions with P&L details
- Pending orders
- Position-level profit/loss tracking

## Installation

### Prerequisites
```bash
# Install required packages
pip install mcp ctrader-open-api twisted python-dotenv pandas numpy
```

### Setup

1. **Configure Environment Variables**

Create a `.env` file in the project root:
```env
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
ACCESS_TOKEN=your_access_token
ACCOUNT_ID=your_account_id
HOST=demo  # or 'live'
```

2. **Get cTrader API Credentials**
   - Visit https://help.ctrader.com/open-api/creating-new-app/
   - Create an application to get CLIENT_ID and CLIENT_SECRET
   - Generate an ACCESS_TOKEN for your account
   - Find your ACCOUNT_ID in cTrader

## Usage

### Running the Server

```bash
python ctrader_mcp_server.py
```

The server will:
1. Connect to cTrader API
2. Authenticate your account
3. Load available symbols
4. Start accepting MCP requests

### Available Tools

#### 1. get_account_status
Get account information including balance, equity, margin, and P&L.

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
    "net_pnl": 248.30
  }
}
```

#### 2. list_symbols
List available trading symbols with optional filtering.

**Parameters:**
- `filter` (optional): Filter text (e.g., "EUR", "BTC")

**Returns:**
```json
{
  "success": true,
  "count": 45,
  "symbols": ["EURUSD", "GBPUSD", "USDJPY", ...]
}
```

#### 3. get_positions
Get all open positions with detailed information.

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
    }
  ]
}
```

#### 4. create_market_order
Create a market order that executes immediately.

**Parameters:**
- `symbol`: Symbol name (e.g., "EURUSD")
- `side`: "BUY" or "SELL"
- `volume`: Volume in lots (e.g., 0.01)
- `stop_loss` (optional): Stop loss price
- `take_profit` (optional): Take profit price

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

#### 5. create_limit_order
Create a limit order that executes at a specified price.

**Parameters:**
- `symbol`: Symbol name
- `side`: "BUY" or "SELL"
- `volume`: Volume in lots
- `price`: Limit price
- `stop_loss` (optional): Stop loss price
- `take_profit` (optional): Take profit price

#### 6. create_stop_order
Create a stop order that triggers at a specified price.

**Parameters:**
- `symbol`: Symbol name
- `side`: "BUY" or "SELL"
- `volume`: Volume in lots
- `price`: Stop trigger price
- `stop_loss` (optional): Stop loss price
- `take_profit` (optional): Take profit price

#### 7. close_position
Close an open position fully or partially.

**Parameters:**
- `position_id`: Position ID to close
- `volume` (optional): Volume to close (closes full position if not specified)

#### 8. cancel_order
Cancel a pending order.

**Parameters:**
- `order_id`: Order ID to cancel

#### 9. get_historical_data
Get historical OHLCV candlestick data.

**Parameters:**
- `symbol`: Symbol name
- `timeframe`: "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", or "MN1"
- `count`: Number of candles (default: 100)

**Returns:**
```json
{
  "success": true,
  "symbol": "EURUSD",
  "timeframe": "H1",
  "count": 100,
  "data": [
    {
      "timestamp": "2025-10-10T10:00:00",
      "open": 1.09000,
      "high": 1.09100,
      "low": 1.08900,
      "close": 1.09050,
      "volume": 12345
    }
  ]
}
```

#### 10. get_indicator
Calculate technical indicators.

**Parameters:**
- `symbol`: Symbol name
- `indicator`: "ema", "sma", "rsi", "macd", "bbands", "atr", or "stochastic"
- `timeframe`: Timeframe (default: "H1")
- `period`: Indicator period (default: 14)

**Example:**
```json
{
  "symbol": "EURUSD",
  "indicator": "rsi",
  "timeframe": "H1",
  "period": 14
}
```

#### 11. get_position_pnl
Get profit/loss details for positions.

**Parameters:**
- `position_id` (optional): Specific position ID (returns all if not specified)

#### 12. subscribe_to_ticks
Subscribe to real-time tick data for a symbol.

**Parameters:**
- `symbol`: Symbol name

#### 13. unsubscribe_from_ticks
Unsubscribe from real-time tick data.

**Parameters:**
- `symbol`: Symbol name

## Integration with AI Assistants

### Claude Desktop Configuration

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ctrader": {
      "command": "python",
      "args": ["/path/to/ctrader-python/ctrader_mcp_server.py"],
      "env": {
        "CLIENT_ID": "your_client_id",
        "CLIENT_SECRET": "your_client_secret",
        "ACCESS_TOKEN": "your_access_token",
        "ACCOUNT_ID": "your_account_id",
        "HOST": "demo"
      }
    }
  }
}
```

### Example Conversations

Once configured, you can interact with the assistant naturally:

**User:** "Show me my account status"
- AI uses `get_account_status` tool

**User:** "Buy 0.01 lots of EURUSD with stop loss at 1.08 and take profit at 1.10"
- AI uses `create_market_order` tool with appropriate parameters

**User:** "What are my open positions?"
- AI uses `get_positions` tool

**User:** "Get the last 50 hourly candles for BTCUSD"
- AI uses `get_historical_data` tool

**User:** "Calculate RSI for EURUSD on the 15-minute chart"
- AI uses `get_indicator` tool

## Safety Features

### Demo vs Live Trading
- Default configuration uses demo accounts
- Explicitly set `HOST=live` in `.env` for live trading
- **Always test on demo before using live accounts**

### Risk Management
- All orders support stop-loss and take-profit parameters
- Volume is specified in lots (0.01 = micro lot)
- Position closing can be partial or full

### Error Handling
- Comprehensive error messages for invalid parameters
- Authentication state checking before operations
- Symbol validation

## Architecture

```
┌─────────────────┐
│  AI Assistant   │
│   (Claude)      │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│  MCP Server     │
│  (Python)       │
└────────┬────────┘
         │
┌────────▼────────┐
│ SimpleCTrader   │
│     Bot         │
└────────┬────────┘
         │ Protobuf/Twisted
         │
┌────────▼────────┐
│  cTrader API    │
│  (Demo/Live)    │
└─────────────────┘
```

## Rate Limits

cTrader API has the following rate limits:
- **50 requests/second** for non-historical data
- **5 requests/second** for historical data

The MCP server automatically manages these limits through the underlying bot implementation.

## Troubleshooting

### Bot not ready
If you get "Bot not ready" errors:
1. Check your `.env` credentials
2. Verify internet connection
3. Ensure cTrader account is active
4. Check logs for authentication errors

### Symbol not found
- Use `list_symbols` to see available symbols
- Symbol names are case-sensitive
- Different brokers may have different symbol names

### Order rejected
- Check account balance and margin
- Verify symbol is tradable
- Ensure volume meets minimum requirements
- Check market hours

## Development

### Adding New Tools

To add new tools:

1. Add tool definition in `handle_list_tools()`
2. Implement handler in `_execute_tool()`
3. Add corresponding method to `SimpleCTraderBot` if needed

### Testing

```bash
# Test with demo account
python ctrader_mcp_server.py

# Monitor logs
tail -f /tmp/ctrader_mcp.log
```

## Resources

- [cTrader Open API Documentation](https://help.ctrader.com/open-api/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [cTrader Python SDK](https://github.com/spotware/OpenApiPy)

## License

This project uses the cTrader Open API and is subject to their terms of use.

## Disclaimer

**Trading involves significant risk. This software is provided "as is" without warranty. Use at your own risk. Always test on demo accounts before live trading.**
