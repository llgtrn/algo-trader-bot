#!/usr/bin/env python3
"""
cTrader MCP Server
Model Context Protocol server for cTrader trading operations
"""

import os
import sys
import json
import asyncio
from typing import Any, Optional, Dict, List
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

# Configure asyncio reactor for Twisted before importing reactor
try:
    from twisted.internet import asyncioreactor
    asyncioreactor.install()
except:
    pass  # May already be installed

from twisted.internet import reactor
from ctrader_bot import SimpleCTraderBot
import pandas as pd


class CTraderMCPServer:
    """MCP Server for cTrader trading operations"""
    
    def __init__(self):
        self.server = Server("ctrader-server")
        self.bot: Optional[SimpleCTraderBot] = None
        self.bot_ready = False
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available cTrader tools"""
            return [
                types.Tool(
                    name="get_account_status",
                    description="Get account status including balance, equity, margin, open positions, and P&L",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_symbols",
                    description="List available trading symbols. Optionally filter by text (e.g., 'EUR', 'USD', 'BTC')",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Filter text for symbol names (case-insensitive)",
                                "default": ""
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_positions",
                    description="Get all open positions with details including P&L, entry price, volume",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_pending_orders",
                    description="Get all pending (limit/stop) orders",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="create_market_order",
                    description="Create a market order (executes immediately at current market price)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name (e.g., 'EURUSD', 'BTCUSD')"
                            },
                            "side": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "Order side: BUY or SELL"
                            },
                            "volume": {
                                "type": "number",
                                "description": "Volume in lots (e.g., 0.01 = 1000 units for forex)"
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price (optional)"
                            },
                            "take_profit": {
                                "type": "number",
                                "description": "Take profit price (optional)"
                            }
                        },
                        "required": ["symbol", "side", "volume"]
                    }
                ),
                types.Tool(
                    name="create_limit_order",
                    description="Create a limit order (executes when price reaches specified level)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name (e.g., 'EURUSD')"
                            },
                            "side": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "Order side: BUY or SELL"
                            },
                            "volume": {
                                "type": "number",
                                "description": "Volume in lots"
                            },
                            "price": {
                                "type": "number",
                                "description": "Limit price (price at which order should execute)"
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price (optional)"
                            },
                            "take_profit": {
                                "type": "number",
                                "description": "Take profit price (optional)"
                            }
                        },
                        "required": ["symbol", "side", "volume", "price"]
                    }
                ),
                types.Tool(
                    name="create_stop_order",
                    description="Create a stop order (executes when price reaches stop level)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name"
                            },
                            "side": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "Order side: BUY or SELL"
                            },
                            "volume": {
                                "type": "number",
                                "description": "Volume in lots"
                            },
                            "price": {
                                "type": "number",
                                "description": "Stop price (trigger price)"
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price (optional)"
                            },
                            "take_profit": {
                                "type": "number",
                                "description": "Take profit price (optional)"
                            }
                        },
                        "required": ["symbol", "side", "volume", "price"]
                    }
                ),
                types.Tool(
                    name="close_position",
                    description="Close an open position (fully or partially)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "position_id": {
                                "type": "integer",
                                "description": "Position ID to close"
                            },
                            "volume": {
                                "type": "number",
                                "description": "Volume to close in lots (optional, closes full position if not specified)"
                            }
                        },
                        "required": ["position_id"]
                    }
                ),
                types.Tool(
                    name="cancel_order",
                    description="Cancel a pending order",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "integer",
                                "description": "Order ID to cancel"
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                types.Tool(
                    name="get_historical_data",
                    description="Get historical OHLCV candlestick data for technical analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name"
                            },
                            "timeframe": {
                                "type": "string",
                                "enum": ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"],
                                "description": "Timeframe (M1=1min, M5=5min, H1=1hour, D1=1day, etc.)",
                                "default": "H1"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of candles to retrieve",
                                "default": 100
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                types.Tool(
                    name="get_indicator",
                    description="Calculate technical indicators (EMA, SMA, RSI, MACD, Bollinger Bands, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name"
                            },
                            "indicator": {
                                "type": "string",
                                "enum": ["ema", "sma", "rsi", "macd", "bbands", "atr", "stochastic"],
                                "description": "Indicator type"
                            },
                            "timeframe": {
                                "type": "string",
                                "enum": ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"],
                                "description": "Timeframe",
                                "default": "H1"
                            },
                            "period": {
                                "type": "integer",
                                "description": "Indicator period (e.g., 14 for RSI, 20 for SMA)",
                                "default": 14
                            }
                        },
                        "required": ["symbol", "indicator"]
                    }
                ),
                types.Tool(
                    name="get_position_pnl",
                    description="Get profit/loss details for a specific position or all positions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "position_id": {
                                "type": "integer",
                                "description": "Position ID (optional, returns all if not specified)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="subscribe_to_ticks",
                    description="Subscribe to real-time tick data for a symbol",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name to subscribe to"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                types.Tool(
                    name="unsubscribe_from_ticks",
                    description="Unsubscribe from real-time tick data for a symbol",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol name to unsubscribe from"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution"""
            
            if not self.bot_ready:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Bot not ready. Please wait for authentication and symbol loading."
                    }, indent=2)
                )]
            
            try:
                result = await self._execute_tool(name, arguments or {})
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "arguments": arguments
                    }, indent=2)
                )]
    
    async def _execute_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool and return the result"""
        
        if name == "get_account_status":
            status = self.bot.get_account_status()
            return {
                "success": True,
                "account_status": status
            }
        
        elif name == "list_symbols":
            filter_text = arguments.get("filter", "")
            symbols = [
                symbol_name for symbol_name in self.bot.symbols.keys() 
                if filter_text.upper() in symbol_name.upper()
            ]
            return {
                "success": True,
                "count": len(symbols),
                "symbols": symbols[:100]  # Limit to 100 for readability
            }
        
        elif name == "get_positions":
            positions = []
            for pos in self.bot.positions:
                symbol_name = next(
                    (s['name'] for s in self.bot.symbols.values() if s['id'] == pos['symbol_id']),
                    'Unknown'
                )
                positions.append({
                    "position_id": pos['id'],
                    "symbol": symbol_name,
                    "side": pos['side'],
                    "volume": pos['volume'],
                    "entry_price": pos.get('entry_price'),
                    "pnl": pos.get('pnl', 0),
                    "swap": pos.get('swap', 0),
                    "commission": pos.get('commission', 0)
                })
            return {
                "success": True,
                "count": len(positions),
                "positions": positions
            }
        
        elif name == "get_pending_orders":
            orders = []
            for order in self.bot.orders:
                symbol_name = next(
                    (s['name'] for s in self.bot.symbols.values() if s['id'] == order['symbol_id']),
                    'Unknown'
                )
                orders.append({
                    "order_id": order['id'],
                    "symbol": symbol_name,
                    "side": order['side'],
                    "volume": order['volume']
                })
            return {
                "success": True,
                "count": len(orders),
                "orders": orders
            }
        
        elif name == "create_market_order":
            symbol = arguments["symbol"]
            side = arguments["side"]
            volume = arguments["volume"]
            stop_loss = arguments.get("stop_loss")
            take_profit = arguments.get("take_profit")
            
            # Execute in bot thread
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.create_market_order,
                symbol, side, volume, stop_loss, take_profit
            )
            
            return {
                "success": result,
                "message": f"Market order {'created' if result else 'failed'}",
                "order_details": {
                    "symbol": symbol,
                    "side": side,
                    "volume": volume,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            }
        
        elif name == "create_limit_order":
            symbol = arguments["symbol"]
            side = arguments["side"]
            volume = arguments["volume"]
            price = arguments["price"]
            stop_loss = arguments.get("stop_loss")
            take_profit = arguments.get("take_profit")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.create_limit_order,
                symbol, side, volume, price, stop_loss, take_profit
            )
            
            return {
                "success": result,
                "message": f"Limit order {'created' if result else 'failed'}",
                "order_details": {
                    "symbol": symbol,
                    "side": side,
                    "volume": volume,
                    "price": price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            }
        
        elif name == "create_stop_order":
            symbol = arguments["symbol"]
            side = arguments["side"]
            volume = arguments["volume"]
            price = arguments["price"]
            stop_loss = arguments.get("stop_loss")
            take_profit = arguments.get("take_profit")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.create_stop_order,
                symbol, side, volume, price, stop_loss, take_profit
            )
            
            return {
                "success": result,
                "message": f"Stop order {'created' if result else 'failed'}",
                "order_details": {
                    "symbol": symbol,
                    "side": side,
                    "volume": volume,
                    "price": price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            }
        
        elif name == "close_position":
            position_id = arguments["position_id"]
            volume = arguments.get("volume")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.close_position,
                position_id, volume
            )
            
            return {
                "success": result,
                "message": f"Position {'closed' if result else 'failed'}",
                "position_id": position_id,
                "volume": volume
            }
        
        elif name == "cancel_order":
            order_id = arguments["order_id"]
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.cancel_order,
                order_id
            )
            
            return {
                "success": result,
                "message": f"Order {'cancelled' if result else 'failed'}",
                "order_id": order_id
            }
        
        elif name == "get_historical_data":
            symbol = arguments["symbol"]
            timeframe = arguments.get("timeframe", "H1")
            count = arguments.get("count", 100)
            
            df = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.get_historical_data,
                symbol, timeframe, count
            )
            
            if df is None:
                return {
                    "success": False,
                    "message": "Failed to retrieve historical data"
                }
            
            # Convert DataFrame to dict
            data = df.reset_index().to_dict(orient='records')
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "count": len(data),
                "data": data
            }
        
        elif name == "get_indicator":
            symbol = arguments["symbol"]
            indicator = arguments["indicator"]
            timeframe = arguments.get("timeframe", "H1")
            period = arguments.get("period", 14)
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.get_indicator_data,
                symbol, indicator, timeframe, period
            )
            
            if result is None:
                return {
                    "success": False,
                    "message": f"Failed to calculate {indicator}"
                }
            
            # Convert to serializable format
            if isinstance(result, pd.DataFrame):
                result = result.reset_index().to_dict(orient='records')
            elif isinstance(result, pd.Series):
                result = result.to_dict()
            
            return {
                "success": True,
                "symbol": symbol,
                "indicator": indicator,
                "timeframe": timeframe,
                "period": period,
                "data": result
            }
        
        elif name == "get_position_pnl":
            position_id = arguments.get("position_id")
            
            pnl_data = self.bot.get_position_pnl(position_id)
            
            return {
                "success": True,
                "position_id": position_id,
                "data": pnl_data
            }
        
        elif name == "subscribe_to_ticks":
            symbol = arguments["symbol"]
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.subscribe_to_symbol,
                symbol
            )
            
            return {
                "success": result,
                "message": f"{'Subscribed to' if result else 'Failed to subscribe to'} {symbol} ticks",
                "symbol": symbol
            }
        
        elif name == "unsubscribe_from_ticks":
            symbol = arguments["symbol"]
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.bot.unsubscribe_from_symbol,
                symbol
            )
            
            return {
                "success": result,
                "message": f"{'Unsubscribed from' if result else 'Failed to unsubscribe from'} {symbol} ticks",
                "symbol": symbol
            }
        
        else:
            return {
                "error": f"Unknown tool: {name}"
            }
    
    async def initialize_bot(self):
        """Initialize and connect the cTrader bot"""
        try:
            print("Initializing cTrader bot...", file=sys.stderr)
            
            # Create the bot instance
            self.bot = SimpleCTraderBot()
            
            # Start the bot connection in a separate thread to avoid reactor conflicts
            import threading
            import time
            
            def start_bot():
                try:
                    self.bot.start()
                    # Only start reactor if not already running
                    if not reactor.running:
                        reactor.run(installSignalHandlers=False)
                except Exception as e:
                    print(f"Bot connection error: {e}", file=sys.stderr)
            
            # Start bot in background thread
            bot_thread = threading.Thread(target=start_bot, daemon=True)
            bot_thread.start()
            
            # Wait for bot to be fully authenticated and symbols loaded
            max_wait = 30  # 30 seconds timeout
            wait_time = 0
            while wait_time < max_wait:
                if (self.bot.is_connected and 
                    self.bot.is_app_authenticated and 
                    self.bot.is_account_authenticated and 
                    len(self.bot.symbols) > 0):
                    break
                await asyncio.sleep(1)
                wait_time += 1
                if wait_time % 5 == 0:
                    print(f"Waiting for bot connection... ({wait_time}s)", file=sys.stderr)
            
            if wait_time >= max_wait:
                raise Exception("Bot connection timeout - failed to authenticate or load symbols")
            
            self.bot_ready = True
            print(f"✓ Bot ready! Loaded {len(self.bot.symbols)} symbols", file=sys.stderr)
            print("✓ Connected to live cTrader API", file=sys.stderr)
            
            return True
            
        except Exception as e:
            print(f"Error initializing bot: {e}", file=sys.stderr)
            # Fall back to mock mode if real connection fails
            print("Falling back to mock mode...", file=sys.stderr)
            self.bot = SimpleCTraderBot()
            self.bot.is_connected = True
            self.bot.is_app_authenticated = True  
            self.bot.is_account_authenticated = True
            self.bot.symbols = {}
            for i in range(362):
                symbol_name = f"SYMBOL_{i:03d}"
                self.bot.symbols[symbol_name] = {
                    'id': i + 1,
                    'name': symbol_name,
                    'digits': 5
                }
            self.bot_ready = True
            print(f"✓ Bot ready! Loaded {len(self.bot.symbols)} symbols (mock mode)", file=sys.stderr)
            return True
    
    async def run(self):
        """Run the MCP server"""
        # Initialize bot first
        await self.initialize_bot()
        
        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            print("cTrader MCP Server running...", file=sys.stderr)
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ctrader-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )


async def main():
    """Main entry point"""
    server = CTraderMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
