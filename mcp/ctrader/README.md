# cTrader MCP Server

A standalone Model Context Protocol (MCP) server that enables AI assistants to interact with the cTrader trading platform.

## 🚀 What is This?

This MCP server allows AI assistants like Claude to execute trades, analyze markets, and manage positions on cTrader through natural language conversations.

**Example conversations:**
- *"Show me my account balance"* → Gets balance, equity, positions
- *"Buy 0.01 lots of EURUSD with stop at 1.08"* → Places trade  
- *"Calculate RSI for GBPUSD"* → Analyzes technical indicators
- *"Close all losing positions"* → Manages risk

## ✨ Features

### Trading Operations
- ✅ **Market Orders** - Execute immediately at current price
- ✅ **Limit Orders** - Order at specific price level
- ✅ **Stop Orders** - Stop-loss or stop-entry orders
- ✅ **Position Management** - Close positions fully or partially
- ✅ **Order Management** - Cancel pending orders

### Market Data & Analysis
- ✅ **Historical Data** - OHLCV candles (9 timeframes: M1, M5, M15, M30, H1, H4, D1, W1, MN1)
- ✅ **Technical Indicators** - RSI, MACD, EMA, SMA, Bollinger Bands, ATR, Stochastic
- ✅ **Real-time Ticks** - Subscribe to live price feeds
- ✅ **Symbol Search** - Browse 100+ trading instruments

### Account Information
- ✅ **Account Status** - Balance, equity, margin, free margin
- ✅ **Position Tracking** - All open positions with P&L
- ✅ **Order Tracking** - All pending orders
- ✅ **P&L Analysis** - Detailed profit/loss breakdown

## 🎯 Available Tools (14 Total)

| Tool | Description |
|------|-------------|
| `get_account_status` | View balance, equity, margin, and P&L |
| `get_positions` | List all open positions with details |
| `get_pending_orders` | Show all pending limit/stop orders |
| `get_position_pnl` | Get detailed P&L breakdown |
| `create_market_order` | Execute trade at current market price |
| `create_limit_order` | Place order at specific price |
| `create_stop_order` | Place stop-loss or stop-entry order |
| `close_position` | Close position fully or partially |
| `cancel_order` | Cancel a pending order |
| `list_symbols` | Browse available trading instruments |
| `get_historical_data` | Get OHLCV candlestick data |
| `get_indicator` | Calculate technical indicators |
| `subscribe_to_ticks` | Subscribe to real-time price updates |
| `unsubscribe_from_ticks` | Unsubscribe from price updates |

## 📋 Prerequisites

- Python 3.10 or higher
- A cTrader account (demo or live)
- cTrader API credentials

## 🔧 Installation

### 1. Get cTrader API Credentials

1. Visit https://help.ctrader.com/open-api/creating-new-app/
2. Create an application to get:
   - `CLIENT_ID`
   - `CLIENT_SECRET`
3. Generate an access token:
   - `ACCESS_TOKEN`
4. Find your account ID in cTrader:
   - `ACCOUNT_ID`

### 2. Install the Server

```bash
# Clone or download this repository
cd ctrader-mcp-server

# Run installation script
./install.sh
```

### 3. Configure Credentials

Create a `.env` file in the project root:

```env
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
ACCESS_TOKEN=your_access_token_here
ACCOUNT_ID=your_account_id_here
HOST=demo
```

**Important:** Use `HOST=demo` for testing!

### 4. Test the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python test_server.py
```

You should see:
```
✓ Bot initialized and authenticated
✓ Account status retrieved
✓ Found X EUR symbols
...
All Tests Completed Successfully! ✓
```

## 🤖 Configure AI Assistant

### Claude Desktop

1. **Find your config file:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add this configuration:**

```json
{
  "mcpServers": {
    "ctrader": {
      "command": "/absolute/path/to/ctrader-mcp-server/venv/bin/python",
      "args": [
        "/absolute/path/to/ctrader-mcp-server/server.py"
      ],
      "cwd": "/absolute/path/to/ctrader-mcp-server"
    }
  }
}
```

3. **Restart Claude Desktop**

### Other MCP Clients

This server implements the standard MCP protocol and should work with any MCP-compatible client.

## 💬 Example Conversations

Once configured, you can interact naturally:

**Check Account:**
> You: "How much money do I have in my cTrader account?"
> 
> AI: "Your account has a balance of $10,000, equity of $10,250, with 3 open positions generating a total P&L of +$250."

**Place Trade:**
> You: "Buy 0.01 lots of EURUSD with stop loss at 1.08 and take profit at 1.10"
> 
> AI: "Order executed! Bought 0.01 lots of EURUSD at 1.09245 with stop loss at 1.08000 and take profit at 1.10000."

**Analyze Market:**
> You: "Calculate the RSI for GBPUSD on the 15-minute chart"
> 
> AI: "GBPUSD RSI(14) on M15 is currently at 65.3, indicating the pair is approaching overbought territory."

**Manage Risk:**
> You: "Close all positions that are losing more than $50"
> 
> AI: "Found 1 position losing more than $50. Closed GBPUSD position (loss: -$62.50)."

## 📚 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Complete Guide](docs/GUIDE.md)** - Comprehensive reference
- **[Architecture](docs/ARCHITECTURE.md)** - Technical details
- **[Configuration](docs/CONFIGURATION.md)** - Setup options
- **[API Reference](docs/API.md)** - All tools documented

## 🔐 Security & Safety

### Demo vs Live Trading
- Default configuration uses **demo accounts**
- Explicitly set `HOST=live` in `.env` for live trading
- **Always test thoroughly on demo before going live**

### Risk Management
- All orders support stop-loss and take-profit
- Position closing can be partial or full
- Volume is specified in lots (0.01 = micro lot)

### Credentials Security
- Credentials stored in `.env` file (never committed)
- Environment variables never exposed in logs
- Authentication state validated before operations

## 🚨 Important Warnings

⚠️ **Trading involves significant risk. You can lose money.**  
⚠️ **Always test on demo accounts first**  
⚠️ **Start with small positions when going live**  
⚠️ **Use stop losses to limit risk**  
⚠️ **Never share your credentials or access tokens**

## 🛠️ Development

### Project Structure

```
ctrader-mcp-server/
├── server.py              # Main MCP server
├── ctrader_bot.py         # cTrader API wrapper
├── test_server.py         # Testing tool
├── install.sh             # Installation script
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
└── docs/                  # Documentation
    ├── QUICKSTART.md
    ├── GUIDE.md
    ├── ARCHITECTURE.md
    ├── CONFIGURATION.md
    └── API.md
```

### Running Tests

```bash
# Basic functionality test
python test_server.py

# Run with specific account
ACCOUNT_ID=12345 python test_server.py

# Test with live account (careful!)
HOST=live python test_server.py
```

### Adding New Tools

To add new tools:

1. Add tool definition in `server.py` `handle_list_tools()`
2. Implement handler in `_execute_tool()`
3. Add corresponding method to `ctrader_bot.py` if needed
4. Update documentation

## 📊 Performance

- **Startup Time:** 5-10 seconds (authentication + symbol loading)
- **Order Execution:** <100ms (market orders)
- **Historical Data:** 1-5 seconds (100 candles)
- **Indicator Calculation:** <1 second
- **Memory Usage:** ~50-100 MB

## 🌐 Rate Limits

cTrader API enforces:
- **50 requests/second** for trading operations
- **5 requests/second** for historical data

The server automatically respects these limits.

## 🐛 Troubleshooting

### "Bot not ready" errors
- Check `.env` file credentials
- Verify internet connection
- Ensure cTrader account is active
- Check server logs for authentication errors

### Symbol not found
- Use `list_symbols` tool to see available symbols
- Symbol names are case-sensitive
- Different brokers may have different symbol names

### Order rejected
- Check account balance and margin
- Verify symbol is tradable
- Ensure volume meets minimum requirements
- Check if market is open

### Connection issues
- Verify API credentials are correct
- Check if account is active
- Ensure no firewall blocking port 5035 (demo) or 5034 (live)

## 🔗 Resources

- [cTrader Open API Documentation](https://help.ctrader.com/open-api/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [cTrader Python SDK](https://github.com/spotware/OpenApiPy)

## 📄 License

MIT License - See LICENSE file for details

## ⚖️ Disclaimer

This software is provided "as is" without warranty of any kind. Trading involves significant risk and you can lose money. Use at your own risk. Always test on demo accounts before live trading.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📧 Support

- 📖 Check the [documentation](docs/)
- 🐛 Report issues on GitHub
- 💬 Join [cTrader Community](https://t.me/ctrader_open_api_support)

---

**Made with ❤️ for algorithmic traders**

**Ready to start?** Run `./install.sh` and follow the instructions above!
