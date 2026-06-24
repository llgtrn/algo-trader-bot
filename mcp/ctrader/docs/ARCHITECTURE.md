# cTrader MCP Server Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Claude     │    │   Browser    │    │   Terminal   │      │
│  │   Desktop    │    │   Client     │    │   CLI        │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                    │              │
└─────────┼───────────────────┼────────────────────┼──────────────┘
          │                   │                    │
          │ MCP Protocol      │ HTTP/REST          │ Direct
          │ (stdio)           │                    │
┌─────────▼───────────────────▼────────────────────▼──────────────┐
│                      INTERFACE LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐    ┌──────────────────────┐           │
│  │  MCP Server          │    │  FastAPI Server      │           │
│  │  ctrader_mcp_server  │    │  api_server.py       │           │
│  │                      │    │                      │           │
│  │  • 14 Tools/Commands │    │  • REST Endpoints    │           │
│  │  • JSON Responses    │    │  • OpenAPI Docs      │           │
│  │  • Async Operations  │    │  • CORS Support      │           │
│  └──────────┬───────────┘    └──────────┬───────────┘           │
│             │                           │                        │
│             └───────────┬───────────────┘                        │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            SimpleCTraderBot                               │   │
│  │            simple_ctrader_bot.py                          │   │
│  │                                                           │   │
│  │  Trading:              Market Data:         Account:     │   │
│  │  • create_market_order • get_historical    • get_status  │   │
│  │  • create_limit_order  • subscribe_ticks   • get_pnl     │   │
│  │  • create_stop_order   • get_indicator     • list_pos    │   │
│  │  • close_position                                        │   │
│  │  • cancel_order                                          │   │
│  │                                                           │   │
│  │  State Management:                                        │   │
│  │  • symbols (dict)                                        │   │
│  │  • positions (list)                                      │   │
│  │  • orders (list)                                         │   │
│  │  • historical_data (cache)                               │   │
│  │  • account_info (dict)                                   │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                    PROTOCOL LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Twisted + cTrader OpenAPI SDK                     │   │
│  │                                                           │   │
│  │  • TcpProtocol (Twisted)                                 │   │
│  │  • Protobuf Message Encoding/Decoding                    │   │
│  │  • Async I/O with Deferreds                              │   │
│  │  • Connection Management                                 │   │
│  │  • Message Routing                                       │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              │ TCP + Protobuf
                              │ Port: 5035 (Demo) / 5034 (Live)
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                      cTrader BACKEND                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  Authentication│  │  Order         │  │  Market Data   │    │
│  │  Service       │  │  Execution     │  │  Service       │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  Position      │  │  Risk          │  │  Historical    │    │
│  │  Management    │  │  Management    │  │  Data          │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### Example 1: Creating a Market Order via MCP

```
1. User → Claude: "Buy 0.01 lots of EURUSD"

2. Claude → MCP Server: 
   Tool: create_market_order
   Args: {symbol: "EURUSD", side: "BUY", volume: 0.01}

3. MCP Server → SimpleCTraderBot:
   bot.create_market_order("EURUSD", "BUY", 0.01)

4. SimpleCTraderBot → cTrader API:
   ProtoOANewOrderReq {
     symbolId: 12345,
     tradeSide: BUY,
     volume: 1000,  // 0.01 lots = 1000 units
     orderType: MARKET
   }

5. cTrader API → SimpleCTraderBot:
   ProtoOAExecutionEvent {
     executionType: ORDER_FILLED,
     orderId: 987654,
     ...
   }

6. SimpleCTraderBot → MCP Server:
   Returns: {success: true, order_id: 987654}

7. MCP Server → Claude:
   JSON response with order details

8. Claude → User:
   "Order executed! Bought 0.01 lots of EURUSD at 1.09245"
```

### Example 2: Getting Account Status

```
1. User → Claude: "How much money do I have?"

2. Claude → MCP Server:
   Tool: get_account_status
   Args: {}

3. MCP Server → SimpleCTraderBot:
   bot.get_account_status()

4. SimpleCTraderBot:
   • Reads cached account_info
   • Calculates P&L from positions
   • Aggregates data

5. SimpleCTraderBot → MCP Server:
   {
     balance: 10000,
     equity: 10250,
     positions_count: 3,
     total_pnl: 250,
     ...
   }

6. MCP Server → Claude:
   JSON response

7. Claude → User:
   "Your account has:
   • Balance: $10,000
   • Equity: $10,250
   • Open Positions: 3
   • Total P&L: +$250"
```

### Example 3: Technical Analysis

```
1. User → Claude: "What's the RSI for GBPUSD?"

2. Claude → MCP Server:
   Tool: get_indicator
   Args: {symbol: "GBPUSD", indicator: "rsi", period: 14}

3. MCP Server → SimpleCTraderBot:
   bot.get_indicator_data("GBPUSD", "rsi", "H1", 14)

4. SimpleCTraderBot:
   a. Checks cache for historical data
   b. If not cached, requests from cTrader API:
      ProtoOAGetTrendbarsReq {
        symbolId: 67890,
        period: H1,
        count: 100
      }
   c. Receives trendbars
   d. Calculates RSI using pandas/numpy

5. SimpleCTraderBot → MCP Server:
   {
     current_rsi: 65.3,
     data: [...historical RSI values...]
   }

6. MCP Server → Claude:
   JSON response with RSI data

7. Claude → User:
   "GBPUSD RSI (14) is currently at 65.3, indicating 
   the pair is approaching overbought territory"
```

## Component Responsibilities

### MCP Server (`ctrader_mcp_server.py`)
- **Input:** MCP tool calls from AI assistant
- **Processing:** Argument validation, async coordination
- **Output:** JSON responses to AI assistant
- **State:** Maintains reference to bot instance
- **Error Handling:** Wraps exceptions in JSON error responses

### SimpleCTraderBot (`simple_ctrader_bot.py`)
- **Input:** Python method calls (from MCP/API/CLI)
- **Processing:** Business logic, caching, calculations
- **Output:** Native Python objects (dicts, lists, DataFrames)
- **State:** Symbols, positions, orders, account info
- **Communication:** Protobuf messages to/from cTrader

### FastAPI Server (`api_server.py`)
- **Input:** HTTP REST requests
- **Processing:** Request validation, response formatting
- **Output:** JSON HTTP responses
- **State:** Shares bot instance with main thread
- **Use Case:** Web UIs, external integrations

## Message Flow Patterns

### Synchronous (CLI)
```
User Input → Bot Method → cTrader API → Response → Print to Console
```

### Asynchronous (MCP)
```
MCP Call → Async Wrapper → Bot Method (in executor) → 
cTrader API → Response → Async Return → JSON Response
```

### Event-Driven (Real-time)
```
cTrader API → Spot Event → Bot Handler → 
Cache Update → Optional Callback
```

## Scalability Considerations

### Current Architecture
- Single bot instance per server
- Single account connection
- Twisted reactor (event-driven, non-blocking)
- Async MCP handlers
- Thread-safe state management

### Potential Enhancements
- Multi-account support (multiple bot instances)
- Connection pooling
- Redis for distributed state
- WebSocket for real-time updates
- Load balancing for multiple MCP clients

## Security Layers

1. **Environment Variables** - Credentials never in code
2. **Demo/Live Separation** - Explicit HOST configuration
3. **State Validation** - Authentication checks before operations
4. **Input Validation** - Type checking, range validation
5. **Error Sanitization** - Safe error messages to users

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| MCP Server | Python MCP SDK | AI assistant protocol |
| REST API | FastAPI | HTTP endpoints |
| Bot Core | Python + Twisted | Async networking |
| cTrader SDK | OpenApiPy | Protobuf messaging |
| Data Processing | Pandas/NumPy | Technical analysis |
| AI Features | Gemini API | Natural language |

## Performance Characteristics

- **Startup Time:** 5-10 seconds (authentication + symbol loading)
- **Order Execution:** <100ms (market orders)
- **Historical Data:** 1-5 seconds (100 candles)
- **Indicator Calculation:** <1 second (most indicators)
- **MCP Tool Call:** 10-500ms (depends on operation)

## Rate Limits

cTrader API limits enforced at protocol layer:
- **50 req/sec** - Trading operations, account queries
- **5 req/sec** - Historical data requests

Bot automatically respects these limits through the SDK.
