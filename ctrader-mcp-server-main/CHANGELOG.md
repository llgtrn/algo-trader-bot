# Changelog

All notable changes to the cTrader MCP Server will be documented in this file.

## [1.0.0] - 2025-10-10

### Added
- Initial release of standalone cTrader MCP Server
- 14 tools for trading, market data, and account management
- Account management tools:
  - get_account_status
  - get_positions
  - get_pending_orders
  - get_position_pnl
- Trading operations tools:
  - create_market_order
  - create_limit_order
  - create_stop_order
  - close_position
  - cancel_order
- Market data and analysis tools:
  - list_symbols
  - get_historical_data
  - get_indicator
  - subscribe_to_ticks
  - unsubscribe_from_ticks
- Technical indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - EMA (Exponential Moving Average)
  - SMA (Simple Moving Average)
  - Bollinger Bands
  - ATR (Average True Range)
  - Stochastic Oscillator
- Support for 9 timeframes (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
- Real-time tick data subscriptions
- Comprehensive documentation
- Installation script
- Testing tool
- Configuration examples for AI assistants

### Features
- Async/await architecture for non-blocking operations
- Twisted reactor integration for cTrader API
- Complete error handling and validation
- Demo and live trading support
- Stop-loss and take-profit support on all orders
- Partial position closing
- Position and order tracking
- Historical data caching

### Documentation
- Quick start guide
- Complete user guide
- Architecture documentation
- Configuration guide
- API reference
- Example configurations for Claude Desktop

### Security
- Environment variable-based credentials
- No hardcoded secrets
- Authentication state validation
- Demo mode by default

### Performance
- Startup time: 5-10 seconds
- Order execution: <100ms
- Historical data: 1-5 seconds (100 candles)
- Memory usage: ~50-100 MB

### Compatibility
- Python 3.10+
- cTrader Open API
- MCP Protocol
- Claude Desktop and other MCP clients

---

## Future Releases

Planned features for future versions:
- Order modification support
- Trailing stop-loss
- Advanced position management
- WebSocket for real-time updates
- Strategy backtesting
- Portfolio analytics
- Multi-account support
- Trade journaling

---

For more information, see [README.md](README.md)
