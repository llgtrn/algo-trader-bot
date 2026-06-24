# cTrader MCP Server - Quick Start Guide

Get started with the cTrader MCP Server in 5 minutes!

## What is This?

The cTrader MCP Server allows AI assistants (like Claude) to trade on your behalf by connecting to the cTrader trading platform. You can have natural conversations with your AI assistant to:

- Check your account balance
- Place trades
- Manage positions
- Analyze market data
- Calculate technical indicators

## Prerequisites

- Python 3.10 or higher
- A cTrader account (demo or live)
- cTrader API credentials

## Step 1: Get cTrader Credentials

1. **Visit**: https://help.ctrader.com/open-api/creating-new-app/
2. **Create an application** to get:
   - `CLIENT_ID`
   - `CLIENT_SECRET`
3. **Generate an access token** for your account:
   - `ACCESS_TOKEN`
4. **Find your account ID** in cTrader:
   - `ACCOUNT_ID`

## Step 2: Install

```bash
# Clone or download the repository
cd /path/to/ctrader-python

# Run installation script
./install_mcp.sh
```

## Step 3: Configure

Create a `.env` file in the project root:

```env
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
ACCESS_TOKEN=your_access_token_here
ACCOUNT_ID=your_account_id_here
HOST=demo
```

**Important:** Use `HOST=demo` for testing!

## Step 4: Test

```bash
# Activate virtual environment
source ctrader_bot_env/bin/activate

# Run test
python test_mcp_server.py
```

You should see:
```
✓ Bot initialized and authenticated
✓ Account status retrieved
✓ Found X EUR symbols
...
All Tests Completed Successfully! ✓
```

## Step 5: Configure AI Assistant

### For Claude Desktop

1. **Find your config file:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add this configuration** (update paths):

```json
{
  "mcpServers": {
    "ctrader": {
      "command": "/absolute/path/to/ctrader-python/ctrader_bot_env/bin/python",
      "args": [
        "/absolute/path/to/ctrader-python/ctrader_mcp_server.py"
      ],
      "cwd": "/absolute/path/to/ctrader-python"
    }
  }
}
```

3. **Restart Claude Desktop**

## Step 6: Try It Out!

Start a conversation with Claude:

**You:** "Show me my cTrader account status"

**Claude:** *Uses the MCP server to retrieve and display your account information*

**You:** "List all EUR currency pairs"

**Claude:** *Shows available EUR symbols*

**You:** "Get the last 50 hourly candles for EURUSD"

**Claude:** *Retrieves and can analyze the historical data*

## Example Conversations

### Check Account
> **You:** "What's my account balance and how many positions do I have?"
>
> **Claude:** Uses `get_account_status` tool

### Place a Trade
> **You:** "Buy 0.01 lots of EURUSD with stop loss at 1.08 and take profit at 1.10"
>
> **Claude:** Uses `create_market_order` tool

### Analyze Market
> **You:** "Calculate the RSI for GBPUSD on the 1-hour chart"
>
> **Claude:** Uses `get_indicator` tool

### Manage Positions
> **You:** "Close all my losing positions"
>
> **Claude:** Uses `get_positions` and `close_position` tools

## Available Commands

The AI assistant can use these tools:

- **Account Management**
  - `get_account_status` - View balance, equity, margin
  - `get_positions` - List open positions
  - `get_pending_orders` - List pending orders
  - `get_position_pnl` - Get P&L details

- **Trading**
  - `create_market_order` - Place market orders
  - `create_limit_order` - Place limit orders
  - `create_stop_order` - Place stop orders
  - `close_position` - Close positions
  - `cancel_order` - Cancel orders

- **Market Data**
  - `list_symbols` - Browse available instruments
  - `get_historical_data` - Get OHLCV candles
  - `get_indicator` - Calculate technical indicators
  - `subscribe_to_ticks` - Real-time price feeds

## Safety Features

✅ **Demo Mode by Default** - Always test with demo account first  
✅ **Stop Loss Support** - All orders support stop-loss  
✅ **Partial Closes** - Can close positions partially  
✅ **Explicit Confirmation** - AI will explain what it's doing

## Common Issues

### "Bot not ready" error
- Check your `.env` file credentials
- Verify cTrader account is active
- Wait 10-20 seconds after starting

### "Symbol not found"
- Use `list_symbols` to see available symbols
- Different brokers have different symbol names
- Try variations (EURUSD vs EUR/USD)

### Orders rejected
- Check account margin
- Verify minimum volume requirements
- Ensure market is open

## Next Steps

- Read the full documentation: `docs/MCP_SERVER_GUIDE.md`
- Learn about technical indicators: `docs/INDICATORS_GUIDE.md`
- Explore trading strategies: `docs/STRATEGY_GUIDE.md`
- See configuration examples: `configs/README.md`

## Important Warnings

⚠️ **Trading involves risk** - You can lose money  
⚠️ **Test thoroughly on demo** before using live accounts  
⚠️ **Start with small positions** when going live  
⚠️ **Use stop losses** to limit risk  
⚠️ **Never share your credentials** or access tokens

## Support

- [cTrader API Documentation](https://help.ctrader.com/open-api/)
- [Model Context Protocol Docs](https://modelcontextprotocol.io/)
- [Project Issues](https://github.com/your-repo/issues)

## License & Disclaimer

This software is provided "as is" without warranty. Trading involves significant risk. Use at your own risk.

---

**Ready to start?** Run `./install_mcp.sh` and follow the steps above!
