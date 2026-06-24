#!/usr/bin/env python3
"""
Test script for cTrader MCP Server
Tests basic functionality without requiring an MCP client
"""

import asyncio
import sys
import os
from server import CTraderMCPServer


async def test_server():
    """Test the MCP server initialization and basic functionality"""
    
    print("="*60)
    print("  cTrader MCP Server Test")
    print("="*60)
    print()
    
    # Check .env file
    if not os.path.exists('.env'):
        print("✗ ERROR: .env file not found!")
        print("  Create a .env file with your cTrader credentials")
        return False
    
    print("✓ .env file found")
    
    # Initialize server
    print("\nInitializing MCP server...")
    try:
        server = CTraderMCPServer()
        print("✓ MCP server created")
    except Exception as e:
        print(f"✗ Failed to create server: {e}")
        return False
    
    # Initialize bot
    print("\nInitializing cTrader bot...")
    try:
        await server.initialize_bot()
        print("✓ Bot initialized and authenticated")
    except Exception as e:
        print(f"✗ Bot initialization failed: {e}")
        return False
    
    # Test getting account status
    print("\n" + "="*60)
    print("  Testing Account Status")
    print("="*60)
    try:
        result = await server._execute_tool("get_account_status", {})
        if result.get("success"):
            print("✓ Account status retrieved")
            status = result.get("account_status", {})
            print(f"  Account ID: {status.get('account_id')}")
            print(f"  Open Positions: {status.get('positions_count', 0)}")
            print(f"  Pending Orders: {status.get('orders_count', 0)}")
            if 'balance' in status:
                print(f"  Balance: ${status.get('balance', 0):,.2f}")
            if 'equity' in status:
                print(f"  Equity: ${status.get('equity', 0):,.2f}")
        else:
            print("✗ Failed to get account status")
            return False
    except Exception as e:
        print(f"✗ Error getting account status: {e}")
        return False
    
    # Test listing symbols
    print("\n" + "="*60)
    print("  Testing Symbol List")
    print("="*60)
    try:
        result = await server._execute_tool("list_symbols", {"filter": "EUR"})
        if result.get("success"):
            count = result.get("count", 0)
            symbols = result.get("symbols", [])
            print(f"✓ Found {count} EUR symbols")
            print(f"  Examples: {', '.join(symbols[:5])}")
        else:
            print("✗ Failed to list symbols")
            return False
    except Exception as e:
        print(f"✗ Error listing symbols: {e}")
        return False
    
    # Test getting positions
    print("\n" + "="*60)
    print("  Testing Positions")
    print("="*60)
    try:
        result = await server._execute_tool("get_positions", {})
        if result.get("success"):
            count = result.get("count", 0)
            print(f"✓ Retrieved {count} open position(s)")
            positions = result.get("positions", [])
            for pos in positions[:5]:  # Show max 5
                print(f"  - {pos['symbol']}: {pos['side']} {pos['volume']} lots, P&L: ${pos.get('pnl', 0):.2f}")
        else:
            print("✗ Failed to get positions")
            return False
    except Exception as e:
        print(f"✗ Error getting positions: {e}")
        return False
    
    # Test getting pending orders
    print("\n" + "="*60)
    print("  Testing Pending Orders")
    print("="*60)
    try:
        result = await server._execute_tool("get_pending_orders", {})
        if result.get("success"):
            count = result.get("count", 0)
            print(f"✓ Retrieved {count} pending order(s)")
            orders = result.get("orders", [])
            for order in orders[:5]:  # Show max 5
                print(f"  - {order['symbol']}: {order['side']} {order['volume']} lots")
        else:
            print("✗ Failed to get orders")
            return False
    except Exception as e:
        print(f"✗ Error getting orders: {e}")
        return False
    
    # Test getting historical data
    print("\n" + "="*60)
    print("  Testing Historical Data")
    print("="*60)
    try:
        result = await server._execute_tool("get_historical_data", {
            "symbol": "EURUSD",
            "timeframe": "H1",
            "count": 10
        })
        if result.get("success"):
            count = result.get("count", 0)
            print(f"✓ Retrieved {count} candles for EURUSD H1")
            data = result.get("data", [])
            if data:
                latest = data[-1]
                print(f"  Latest: O:{latest.get('open'):.5f} H:{latest.get('high'):.5f} "
                      f"L:{latest.get('low'):.5f} C:{latest.get('close'):.5f}")
        else:
            print("✗ Failed to get historical data")
            print(f"  Message: {result.get('message')}")
            # Don't fail test - some symbols might not be available
    except Exception as e:
        print(f"✗ Error getting historical data: {e}")
        # Don't fail test
    
    print("\n" + "="*60)
    print("  All Tests Completed Successfully! ✓")
    print("="*60)
    print()
    print("The MCP server is working correctly.")
    print("You can now configure it with your AI assistant.")
    print()
    
    # Cleanup
    if server.bot:
        server.bot.stop()
    
    return True


async def main():
    """Main test entry point"""
    try:
        success = await test_server()
        # Give time for cleanup
        await asyncio.sleep(2)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
