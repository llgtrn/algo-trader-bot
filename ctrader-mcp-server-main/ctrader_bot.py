#!/usr/bin/env python3
"""
Simple cTrader Bot
A minimal bot to create and close orders using cTrader Open API
"""

import os
import sys
from twisted.internet import reactor
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from dotenv import load_dotenv
import time
import pandas as pd
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

class SimpleCTraderBot:
    """Simple trading bot for cTrader API"""
    
    def __init__(self):
        # Load credentials from .env
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.access_token = os.getenv('ACCESS_TOKEN')
        self.account_id = int(os.getenv('ACCOUNT_ID', '0'))
        self.host_type = os.getenv('HOST', 'demo').lower()
        
        # Validate credentials
        if not all([self.client_id, self.client_secret, self.access_token, self.account_id]):
            raise ValueError("Missing credentials in .env file")
        
        # State
        self.client = None
        self.is_connected = False
        self.is_app_authenticated = False
        self.is_account_authenticated = False
        self.symbols = {}
        self.positions = []
        self.orders = []
        self.historical_data = {}  # Cache for historical data
        self.tick_subscribers = set()  # Active tick subscriptions
        self.account_info = {}  # Account balance, equity, margin info
        
        print(f"✓ Bot initialized (Host: {self.host_type}, Account: {self.account_id})")
    
    def start(self):
        """Connect to cTrader API"""
        host = EndPoints.PROTOBUF_LIVE_HOST if self.host_type == "live" else EndPoints.PROTOBUF_DEMO_HOST
        self.client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        
        # Set up callbacks
        self.client.setConnectedCallback(self._on_connected)
        self.client.setDisconnectedCallback(self._on_disconnected)
        self.client.setMessageReceivedCallback(self._on_message)
        
        # Start the client
        self.client.startService()
        print(f"Connecting to {host}:{EndPoints.PROTOBUF_PORT}...")
    
    def _on_connected(self, client):
        """Called when connected to server"""
        print("✓ Connected to cTrader server")
        self.is_connected = True
        
        # Send application authentication request
        request = ProtoOAApplicationAuthReq()
        request.clientId = self.client_id
        request.clientSecret = self.client_secret
        
        deferred = client.send(request)
        deferred.addErrback(self._on_error)
        print("Authenticating application...")
    
    def _on_disconnected(self, client, reason):
        """Called when disconnected from server"""
        print(f"✗ Disconnected: {reason}")
        self.is_connected = False
        self.is_app_authenticated = False
        self.is_account_authenticated = False
    
    def _on_message(self, client, message):
        """Handle incoming messages"""
        try:
            # Application authentication response
            if message.payloadType == ProtoOAApplicationAuthRes().payloadType:
                print("✓ Application authenticated")
                self.is_app_authenticated = True
                self._authenticate_account()
            
            # Account authentication response
            elif message.payloadType == ProtoOAAccountAuthRes().payloadType:
                print("✓ Account authenticated")
                self.is_account_authenticated = True
                self._request_symbols()
            
            # Symbols list response
            elif message.payloadType == ProtoOASymbolsListRes().payloadType:
                self._handle_symbols_response(message)
            
            # Execution event (order/position updates)
            elif message.payloadType == ProtoOAExecutionEvent().payloadType:
                self._handle_execution_event(message)
            
            # Order error event
            elif message.payloadType == ProtoOAOrderErrorEvent().payloadType:
                self._handle_order_error(message)
            
            # Reconcile response (positions and orders)
            elif message.payloadType == ProtoOAReconcileRes().payloadType:
                self._handle_reconcile_response(message)
            
            # Spot (tick) event
            elif message.payloadType == ProtoOASpotEvent().payloadType:
                self._handle_spot_event(message)
            
            # Historical data (trendbars) response
            elif message.payloadType == ProtoOAGetTrendbarsRes().payloadType:
                self._handle_trendbars_response(message)
            
        except Exception as e:
            print(f"✗ Error processing message: {e}")
    
    def _authenticate_account(self):
        """Authenticate trading account"""
        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = self.account_id
        request.accessToken = self.access_token
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        print("Authenticating account...")
    
    def _request_symbols(self):
        """Request available symbols"""
        request = ProtoOASymbolsListReq()
        request.ctidTraderAccountId = self.account_id
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
    
    def _handle_symbols_response(self, message):
        """Process symbols list"""
        response = Protobuf.extract(message)
        for symbol in response.symbol:
            self.symbols[symbol.symbolName] = {
                'id': symbol.symbolId,
                'name': symbol.symbolName,
                'digits': getattr(symbol, 'digits', 5)
            }
        print(f"✓ Loaded {len(self.symbols)} symbols")
        
        # Debug: Print first few symbols to verify real symbol names
        if len(self.symbols) > 0:
            symbol_names = list(self.symbols.keys())[:10]
            print(f"First 10 symbols: {symbol_names}")
        
        # Request current positions and orders
        self.refresh_positions()
    
    def _handle_execution_event(self, message):
        """Handle order/position execution events"""
        event = Protobuf.extract(message)
        exec_type = event.executionType
        
        if exec_type == ProtoOAExecutionType.ORDER_ACCEPTED:
            print(f"✓ Order accepted: {event.order.orderId}")
        elif exec_type == ProtoOAExecutionType.ORDER_FILLED:
            print(f"✓ Order filled: {event.order.orderId}")
        elif exec_type == ProtoOAExecutionType.ORDER_CANCELLED:
            print(f"✓ Order cancelled: {event.order.orderId}")
        elif exec_type == ProtoOAExecutionType.ORDER_REJECTED:
            print(f"✗ Order rejected: {event.order.orderId}")
    
    def _handle_order_error(self, message):
        """Handle order errors"""
        error = Protobuf.extract(message)
        print(f"✗ Order error: {error.errorCode} - {error.description}")
    
    def _handle_reconcile_response(self, message):
        """Process positions and orders"""
        response = Protobuf.extract(message)
        
        # Extract account info if available
        if hasattr(response, 'balance'):
            self.account_info['balance'] = response.balance / 100  # Convert from cents
        if hasattr(response, 'equity'):
            self.account_info['equity'] = response.equity / 100
        if hasattr(response, 'margin'):
            self.account_info['margin'] = response.margin / 100
        if hasattr(response, 'freeMargin'):
            self.account_info['free_margin'] = response.freeMargin / 100
        
        self.positions = []
        for pos in response.position:
            # Get symbol info for proper conversion
            symbol_info = next((s for s in self.symbols.values() if s['id'] == pos.tradeData.symbolId), None)
            
            self.positions.append({
                'id': pos.positionId,
                'symbol_id': pos.tradeData.symbolId,
                'volume': pos.tradeData.volume / 100,  # Convert from centilots
                'side': 'BUY' if pos.tradeData.tradeSide == ProtoOATradeSide.BUY else 'SELL',
                'entry_price': pos.price,
                'swap': getattr(pos, 'swap', 0) / 100,  # Convert from cents
                'commission': getattr(pos, 'commission', 0) / 100,  # Convert from cents
                'pnl': getattr(pos, 'moneyDigits', getattr(pos, 'grossProfit', 0)) / 100  # Try both fields
            })
        
        self.orders = []
        for order in response.order:
            self.orders.append({
                'id': order.orderId,
                'symbol_id': order.tradeData.symbolId,
                'volume': order.tradeData.volume / 100,
                'side': 'BUY' if order.tradeData.tradeSide == ProtoOATradeSide.BUY else 'SELL'
            })
        
        print(f"✓ Positions: {len(self.positions)}, Orders: {len(self.orders)}")
    
    def _handle_spot_event(self, message):
        """Handle real-time tick data"""
        response = Protobuf.extract(message)
        symbol_name = next((s['name'] for s in self.symbols.values() if s['id'] == response.symbolId), 'Unknown')
        
        # Print tick data (you can customize this or add callbacks)
        print(f"Tick: {symbol_name} | Bid: {response.bid / 100000:.5f} | Ask: {response.ask / 100000:.5f}")
    
    def _handle_trendbars_response(self, message):
        """Handle historical trendbar data"""
        response = Protobuf.extract(message)
        
        if not hasattr(response, 'trendbar') or len(response.trendbar) == 0:
            return
        
        symbol_name = next((s['name'] for s in self.symbols.values() if s['id'] == response.symbolId), 'Unknown')
        
        # Get symbol digits for proper price conversion
        symbol_info = self.symbols.get(symbol_name.upper(), {})
        digits = symbol_info.get('digits', 5)
        divisor = 10 ** digits
        
        # Convert to DataFrame
        data = []
        for bar in response.trendbar:
            # cTrader uses delta encoding: low is the base, other prices are deltas
            low_price = bar.low / divisor
            
            data.append({
                'timestamp': pd.to_datetime(bar.utcTimestampInMinutes * 60, unit='s'),
                'open': low_price + (bar.deltaOpen / divisor if hasattr(bar, 'deltaOpen') else 0),
                'high': low_price + (bar.deltaHigh / divisor if hasattr(bar, 'deltaHigh') else 0),
                'low': low_price,
                'close': low_price + (bar.deltaClose / divisor if hasattr(bar, 'deltaClose') else 0),
                'volume': bar.volume if hasattr(bar, 'volume') else 0
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Cache the data based on symbol and period
        period_map = {v: k for k, v in {
            'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
            'H1': 60, 'H4': 240, 'D1': 1440, 'W1': 10080, 'MN1': 43200
        }.items()}
        
        period_name = period_map.get(response.period, 'H1')
        cache_key = f"{symbol_name}_{period_name}"
        self.historical_data[cache_key] = df
        
        print(f"✓ Retrieved {len(df)} candles for {symbol_name} ({period_name})")
    
    def _on_error(self, failure):
        """Handle errors"""
        print(f"✗ Error: {failure}")
    
    def get_symbol_id(self, symbol_name):
        """Get symbol ID by name"""
        symbol = self.symbols.get(symbol_name.upper())
        if symbol:
            return symbol['id']
        return None
    
    def create_market_order(self, symbol_name, side, volume, stop_loss=None, take_profit=None):
        """
        Create a market order
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            side: 'BUY' or 'SELL'
            volume: Volume in lots (e.g., 0.01)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return False
        
        symbol_id = self.get_symbol_id(symbol_name)
        if not symbol_id:
            print(f"✗ Symbol '{symbol_name}' not found")
            return False
        
        request = ProtoOANewOrderReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId = symbol_id
        request.orderType = ProtoOAOrderType.MARKET
        request.tradeSide = ProtoOATradeSide.BUY if side.upper() == 'BUY' else ProtoOATradeSide.SELL
        request.volume = int(volume * 100)  # Convert to centilots
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request.stopLoss = stop_loss
        if take_profit is not None:
            request.takeProfit = take_profit
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        
        sl_tp_info = []
        if stop_loss:
            sl_tp_info.append(f"SL: {stop_loss}")
        if take_profit:
            sl_tp_info.append(f"TP: {take_profit}")
        sl_tp_str = f" ({', '.join(sl_tp_info)})" if sl_tp_info else ""
        
        print(f"→ Creating {side} market order: {volume} lots of {symbol_name}{sl_tp_str}")
        return True
    
    def create_limit_order(self, symbol_name, side, volume, price, stop_loss=None, take_profit=None):
        """
        Create a limit order (pending order at specific price)
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            side: 'BUY' or 'SELL'
            volume: Volume in lots (e.g., 0.01)
            price: Limit price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return False
        
        symbol_id = self.get_symbol_id(symbol_name)
        if not symbol_id:
            print(f"✗ Symbol '{symbol_name}' not found")
            return False
        
        request = ProtoOANewOrderReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId = symbol_id
        request.orderType = ProtoOAOrderType.LIMIT
        request.tradeSide = ProtoOATradeSide.BUY if side.upper() == 'BUY' else ProtoOATradeSide.SELL
        request.volume = int(volume * 100)  # Convert to centilots
        
        # Set limit price (in pips)
        symbol_info = self.symbols.get(symbol_name.upper())
        if symbol_info and 'digits' in symbol_info:
            digits = symbol_info['digits']
            request.limitPrice = int(price * (10 ** digits))
        else:
            # Default to 5 digits if symbol info not available
            request.limitPrice = int(price * 100000)
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request.stopLoss = stop_loss
        if take_profit is not None:
            request.takeProfit = take_profit
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        
        sl_tp_info = []
        if stop_loss:
            sl_tp_info.append(f"SL: {stop_loss}")
        if take_profit:
            sl_tp_info.append(f"TP: {take_profit}")
        sl_tp_str = f" ({', '.join(sl_tp_info)})" if sl_tp_info else ""
        
        print(f"→ Creating {side} limit order: {volume} lots of {symbol_name} @ {price}{sl_tp_str}")
        return True
    
    def create_stop_order(self, symbol_name, side, volume, price, stop_loss=None, take_profit=None):
        """
        Create a stop order (pending order triggered when price reaches level)
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            side: 'BUY' or 'SELL'
            volume: Volume in lots (e.g., 0.01)
            price: Stop price (trigger price)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return False
        
        symbol_id = self.get_symbol_id(symbol_name)
        if not symbol_id:
            print(f"✗ Symbol '{symbol_name}' not found")
            return False
        
        request = ProtoOANewOrderReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId = symbol_id
        request.orderType = ProtoOAOrderType.STOP
        request.tradeSide = ProtoOATradeSide.BUY if side.upper() == 'BUY' else ProtoOATradeSide.SELL
        request.volume = int(volume * 100)  # Convert to centilots
        
        # Set stop price (in pips)
        symbol_info = self.symbols.get(symbol_name.upper())
        if symbol_info and 'digits' in symbol_info:
            digits = symbol_info['digits']
            request.stopPrice = int(price * (10 ** digits))
        else:
            # Default to 5 digits if symbol info not available
            request.stopPrice = int(price * 100000)
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request.stopLoss = stop_loss
        if take_profit is not None:
            request.takeProfit = take_profit
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        
        sl_tp_info = []
        if stop_loss:
            sl_tp_info.append(f"SL: {stop_loss}")
        if take_profit:
            sl_tp_info.append(f"TP: {take_profit}")
        sl_tp_str = f" ({', '.join(sl_tp_info)})" if sl_tp_info else ""
        
        print(f"→ Creating {side} stop order: {volume} lots of {symbol_name} @ {price}{sl_tp_str}")
        return True
    
    def close_position(self, position_id, volume=None):
        """
        Close a position (fully or partially)
        
        Args:
            position_id: Position ID
            volume: Volume to close in lots (None = close all)
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return False
        
        # Find position
        position = next((p for p in self.positions if p['id'] == position_id), None)
        if not position:
            print(f"✗ Position {position_id} not found")
            return False
        
        # Use full volume if not specified
        if volume is None:
            volume = position['volume']
        
        request = ProtoOAClosePositionReq()
        request.ctidTraderAccountId = self.account_id
        request.positionId = position_id
        request.volume = int(volume * 100)  # Convert to centilots
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        
        print(f"→ Closing position {position_id}: {volume} lots")
        return True
    
    def cancel_order(self, order_id):
        """
        Cancel a pending order
        
        Args:
            order_id: Order ID to cancel
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return False
        
        # Find order
        order = next((o for o in self.orders if o['id'] == order_id), None)
        if not order:
            print(f"✗ Order {order_id} not found")
            return False
        
        request = ProtoOACancelOrderReq()
        request.ctidTraderAccountId = self.account_id
        request.orderId = order_id
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        
        print(f"→ Cancelling order {order_id}")
        return True
    
    def list_orders(self):
        """List all pending orders"""
        if not self.orders:
            print("=== PENDING ORDERS ===")
            print("No pending orders")
            return
        
        print("=== PENDING ORDERS ===")
        for order in self.orders:
            symbol_name = next((s['name'] for s in self.symbols.values() if s['id'] == order['symbol_id']), 'Unknown')
            print(f"ID: {order['id']} | {symbol_name} | {order['side']} | {order['volume']} lots")
    
    def refresh_positions(self):
        """Refresh positions and orders from server"""
        if not self.is_account_authenticated:
            return
        
        request = ProtoOAReconcileReq()
        request.ctidTraderAccountId = self.account_id
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
    
    def list_positions(self):
        """Print current positions"""
        if not self.positions:
            print("No open positions")
            return
        
        print("\n=== OPEN POSITIONS ===")
        for pos in self.positions:
            symbol_name = next((s['name'] for s in self.symbols.values() if s['id'] == pos['symbol_id']), 'Unknown')
            print(f"ID: {pos['id']} | {symbol_name} | {pos['side']} | {pos['volume']} lots | Entry: {pos['entry_price']}")
    
    def list_symbols(self, filter_text=''):
        """List available symbols"""
        symbols = [s['name'] for s in self.symbols.values() if filter_text.upper() in s['name']]
        if symbols:
            print(f"\nAvailable symbols ({len(symbols)}):")
            for i, sym in enumerate(symbols[:20], 1):
                print(f"{i}. {sym}")
            if len(symbols) > 20:
                print(f"... and {len(symbols) - 20} more")
        else:
            print("No symbols found")
    
    def get_historical_data(self, symbol_name, timeframe='H1', count=100):
        """
        Get historical OHLCV data for a symbol
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, etc.)
            count: Number of candles to retrieve
            
        Returns:
            pd.DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return None
        
        symbol_id = self.get_symbol_id(symbol_name)
        if not symbol_id:
            print(f"✗ Symbol '{symbol_name}' not found")
            return None
        
        # Map timeframe string to ProtoOATimeInForce value
        timeframe_map = {
            'M1': ProtoOATrendbarPeriod.M1,
            'M5': ProtoOATrendbarPeriod.M5,
            'M15': ProtoOATrendbarPeriod.M15,
            'M30': ProtoOATrendbarPeriod.M30,
            'H1': ProtoOATrendbarPeriod.H1,
            'H4': ProtoOATrendbarPeriod.H4,
            'D1': ProtoOATrendbarPeriod.D1,
            'W1': ProtoOATrendbarPeriod.W1,
            'MN1': ProtoOATrendbarPeriod.MN1,
        }
        
        if timeframe not in timeframe_map:
            print(f"✗ Invalid timeframe. Use: {', '.join(timeframe_map.keys())}")
            return None
        
        # Calculate timestamps
        to_timestamp = int(time.time() * 1000)  # Current time in milliseconds
        
        request = ProtoOAGetTrendbarsReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId = symbol_id
        request.period = timeframe_map[timeframe]
        request.fromTimestamp = to_timestamp - (count * self._get_period_ms(timeframe))
        request.toTimestamp = to_timestamp
        request.count = count
        
        # Store the request callback
        def handle_trendbars(message):
            response = Protobuf.extract(message)
            
            if not hasattr(response, 'trendbar') or len(response.trendbar) == 0:
                print(f"✗ No data received for {symbol_name}")
                return None
            
            # Get symbol digits for proper price conversion
            symbol_info = self.symbols.get(symbol_name.upper(), {})
            digits = symbol_info.get('digits', 5)
            divisor = 10 ** digits
            
            # Convert to DataFrame
            data = []
            for bar in response.trendbar:
                try:
                    # cTrader uses delta encoding: low is the base, other prices are deltas
                    timestamp = pd.to_datetime(bar.utcTimestampInMinutes * 60, unit='s')
                    low_price = bar.low / divisor
                    
                    data.append({
                        'timestamp': timestamp,
                        'open': low_price + (bar.deltaOpen / divisor if hasattr(bar, 'deltaOpen') else 0),
                        'high': low_price + (bar.deltaHigh / divisor if hasattr(bar, 'deltaHigh') else 0),
                        'low': low_price,
                        'close': low_price + (bar.deltaClose / divisor if hasattr(bar, 'deltaClose') else 0),
                        'volume': bar.volume if hasattr(bar, 'volume') else 0
                    })
                except (AttributeError, ValueError) as e:
                    # Skip bars with invalid data
                    continue
            
            if not data:
                print(f"✗ No valid data received for {symbol_name}")
                return None
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            # Cache the data
            cache_key = f"{symbol_name}_{timeframe}"
            self.historical_data[cache_key] = df
            
            print(f"✓ Retrieved {len(df)} candles for {symbol_name} ({timeframe})")
            return df
        
        deferred = self.client.send(request)
        deferred.addCallback(handle_trendbars)
        deferred.addErrback(self._on_error)
        
        # Return cached data if available while waiting for new data
        cache_key = f"{symbol_name}_{timeframe}"
        return self.historical_data.get(cache_key)
    
    def _get_period_ms(self, timeframe):
        """Get period in milliseconds for a timeframe"""
        periods = {
            'M1': 60 * 1000,
            'M5': 5 * 60 * 1000,
            'M15': 15 * 60 * 1000,
            'M30': 30 * 60 * 1000,
            'H1': 60 * 60 * 1000,
            'H4': 4 * 60 * 60 * 1000,
            'D1': 24 * 60 * 60 * 1000,
            'W1': 7 * 24 * 60 * 60 * 1000,
            'MN1': 30 * 24 * 60 * 60 * 1000,
        }
        return periods.get(timeframe, 60 * 60 * 1000)
    
    def subscribe_to_ticks(self, symbol_name, callback=None):
        """
        Subscribe to real-time tick data for a symbol
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            callback: Optional callback function(tick_data) to call on each tick
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return False
        
        symbol_id = self.get_symbol_id(symbol_name)
        if not symbol_id:
            print(f"✗ Symbol '{symbol_name}' not found")
            return False
        
        request = ProtoOASubscribeSpotsReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId.append(symbol_id)
        
        deferred = self.client.send(request)
        deferred.addErrback(self._on_error)
        
        self.tick_subscribers.add(symbol_name)
        print(f"✓ Subscribed to {symbol_name} ticks")
        return True
    
    def unsubscribe_from_ticks(self, symbol_name):
        """Unsubscribe from tick data"""
        if symbol_name in self.tick_subscribers:
            symbol_id = self.get_symbol_id(symbol_name)
            if symbol_id:
                request = ProtoOAUnsubscribeSpotsReq()
                request.ctidTraderAccountId = self.account_id
                request.symbolId.append(symbol_id)
                
                deferred = self.client.send(request)
                deferred.addErrback(self._on_error)
                
                self.tick_subscribers.remove(symbol_name)
                print(f"✓ Unsubscribed from {symbol_name} ticks")
    
    def get_indicator_data(self, symbol_name, indicator='ema', timeframe='H1', period=14, **kwargs):
        """
        Calculate technical indicator for a symbol
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            indicator: Indicator name ('ema', 'sma', 'macd', 'rsi', 'bollinger', 'cci', 'atr', etc.)
            timeframe: Timeframe for historical data
            period: Indicator period
            **kwargs: Additional indicator-specific parameters
            
        Returns:
            Calculated indicator data
        """
        from indicators import TechnicalIndicators
        
        # Get historical data
        df = self.get_historical_data(symbol_name, timeframe, count=max(200, period * 3))
        
        if df is None or df.empty:
            print(f"✗ No historical data available for {symbol_name}")
            return None
        
        # Calculate indicator
        try:
            if indicator.lower() == 'ema':
                return TechnicalIndicators.ema(df['close'], period)
            
            elif indicator.lower() == 'sma':
                return TechnicalIndicators.sma(df['close'], period)
            
            elif indicator.lower() == 'macd':
                fast = kwargs.get('fast', 12)
                slow = kwargs.get('slow', 26)
                signal = kwargs.get('signal', 9)
                return TechnicalIndicators.macd(df['close'], fast, slow, signal)
            
            elif indicator.lower() == 'rsi':
                return TechnicalIndicators.rsi(df['close'], period)
            
            elif indicator.lower() == 'bollinger':
                std_dev = kwargs.get('std_dev', 2.0)
                return TechnicalIndicators.bollinger_bands(df['close'], period, std_dev)
            
            elif indicator.lower() == 'cci':
                return TechnicalIndicators.cci(df['high'], df['low'], df['close'], period)
            
            elif indicator.lower() == 'atr':
                return TechnicalIndicators.atr(df['high'], df['low'], df['close'], period)
            
            elif indicator.lower() == 'chaikin':
                ema_period = kwargs.get('ema_period', 10)
                change_period = kwargs.get('change_period', 10)
                return TechnicalIndicators.chaikin_volatility(df['high'], df['low'], ema_period, change_period)
            
            elif indicator.lower() == 'stochastic':
                d_period = kwargs.get('d_period', 3)
                return TechnicalIndicators.stochastic(df['high'], df['low'], df['close'], period, d_period)
            
            elif indicator.lower() == 'adx':
                return TechnicalIndicators.adx(df['high'], df['low'], df['close'], period)
            
            elif indicator.lower() == 'obv':
                return TechnicalIndicators.obv(df['close'], df['volume'])
            
            elif indicator.lower() == 'vwap':
                return TechnicalIndicators.vwap(df['high'], df['low'], df['close'], df['volume'])
            
            else:
                print(f"✗ Unknown indicator: {indicator}")
                print("Available: ema, sma, macd, rsi, bollinger, cci, atr, chaikin, stochastic, adx, obv, vwap")
                return None
                
        except Exception as e:
            print(f"✗ Error calculating {indicator}: {e}")
            return None
    
    def get_account_status(self):
        """
        Get account status including balance, equity, margin, PnL
        
        Returns:
            dict: Account information
        """
        if not self.is_account_authenticated:
            print("✗ Not authenticated")
            return None
        
        # Calculate total PnL from positions
        total_pnl = sum(pos.get('pnl', 0) for pos in self.positions)
        total_swap = sum(pos.get('swap', 0) for pos in self.positions)
        total_commission = sum(pos.get('commission', 0) for pos in self.positions)
        
        status = {
            'account_id': self.account_id,
            'positions_count': len(self.positions),
            'orders_count': len(self.orders),
            'total_pnl': total_pnl,
            'total_swap': total_swap,
            'total_commission': total_commission,
            'net_pnl': total_pnl + total_swap + total_commission
        }
        
        # Add cached account info if available
        if self.account_info:
            status.update(self.account_info)
        
        return status
    
    def print_account_status(self):
        """Print formatted account status"""
        status = self.get_account_status()
        
        if not status:
            return
        
        print("\n" + "="*60)
        print("ACCOUNT STATUS")
        print("="*60)
        print(f"Account ID:        {status['account_id']}")
        print(f"Open Positions:    {status['positions_count']}")
        print(f"Pending Orders:    {status['orders_count']}")
        print("-"*60)
        
        # Financial info
        if 'balance' in status:
            print(f"Balance:           ${status['balance']:,.2f}")
        if 'equity' in status:
            print(f"Equity:            ${status['equity']:,.2f}")
        if 'margin' in status:
            print(f"Used Margin:       ${status['margin']:,.2f}")
        if 'free_margin' in status:
            print(f"Free Margin:       ${status['free_margin']:,.2f}")
        
        print("-"*60)
        print(f"Total P&L:         ${status['total_pnl']:,.2f}")
        print(f"Total Swap:        ${status['total_swap']:,.2f}")
        print(f"Total Commission:  ${status['total_commission']:,.2f}")
        print(f"Net P&L:           ${status['net_pnl']:,.2f}")
        print("="*60 + "\n")
    
    def get_position_pnl(self, position_id=None):
        """
        Get P&L for a specific position or all positions
        
        Args:
            position_id: Position ID (optional). If None, returns all positions' PnL
        
        Returns:
            float or list: P&L value(s)
        """
        if position_id is None:
            # Return all positions with PnL
            pnl_list = []
            for pos in self.positions:
                symbol_name = next((s['name'] for s in self.symbols.values() if s['id'] == pos['symbol_id']), 'Unknown')
                pnl_list.append({
                    'id': pos['id'],
                    'symbol': symbol_name,
                    'side': pos['side'],
                    'volume': pos['volume'],
                    'pnl': pos.get('pnl', 0),
                    'swap': pos.get('swap', 0),
                    'commission': pos.get('commission', 0)
                })
            return pnl_list
        else:
            # Return specific position PnL
            position = next((p for p in self.positions if p['id'] == position_id), None)
            if position:
                return {
                    'pnl': position.get('pnl', 0),
                    'swap': position.get('swap', 0),
                    'commission': position.get('commission', 0)
                }
            return None
    
    def stop(self):
        """Stop the bot"""
        print("\nShutting down...")
        if self.client:
            self.client.stopService()
        if reactor.running:
            reactor.stop()


def main():
    """Main entry point"""
    print("=== Simple cTrader Bot ===\n")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("✗ .env file not found!")
        print("Please create a .env file with your credentials.")
        print("See .env.example for reference.")
        return 1
    
    try:
        # Create and start bot
        bot = SimpleCTraderBot()
        bot.start()
        
        # Example: Wait for authentication and show menu
        def show_menu():
            if bot.is_account_authenticated:
                print("\n" + "="*50)
                print("BOT READY - Available commands:")
                print("="*50)
                print("  Python console is active. Use bot methods:")
                print("  bot.list_symbols('EUR')      - List symbols")
                print("  bot.create_market_order('EURUSD', 'BUY', 0.01)")
                print("  bot.list_positions()         - Show positions")
                print("  bot.close_position(pos_id)   - Close position")
                print("  bot.refresh_positions()      - Refresh data")
                print("  bot.stop()                   - Stop bot")
                print("="*50 + "\n")
        
        # Schedule menu display
        reactor.callLater(5, show_menu)
        
        # Run reactor
        reactor.run()
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        return 0
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
