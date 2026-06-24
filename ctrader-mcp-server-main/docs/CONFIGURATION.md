# cTrader MCP Server Configuration Examples

This directory contains example configuration files for integrating the cTrader MCP server with various AI assistants.

## Claude Desktop

**File:** `claude_desktop_config.json`

**Location (macOS):**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Location (Windows):**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Location (Linux):**
```
~/.config/Claude/claude_desktop_config.json
```

### Setup Steps:

1. Copy the example config to the appropriate location
2. Update the `args` path to point to your `ctrader_mcp_server.py`
3. Replace the placeholder credentials with your actual cTrader API credentials
4. Restart Claude Desktop

### Example Config:

```json
{
  "mcpServers": {
    "ctrader": {
      "command": "python",
      "args": [
        "/absolute/path/to/ctrader-python/ctrader_mcp_server.py"
      ],
      "env": {
        "CLIENT_ID": "your_client_id",
        "CLIENT_SECRET": "your_client_secret",
        "ACCESS_TOKEN": "your_access_token",
        "ACCOUNT_ID": "123456",
        "HOST": "demo"
      }
    }
  }
}
```

## Using Virtual Environment

If you're using a virtual environment, use the Python interpreter from that environment:

```json
{
  "mcpServers": {
    "ctrader": {
      "command": "/absolute/path/to/ctrader-python/ctrader_bot_env/bin/python",
      "args": [
        "/absolute/path/to/ctrader-python/ctrader_mcp_server.py"
      ],
      "env": {
        "CLIENT_ID": "your_client_id",
        "CLIENT_SECRET": "your_client_secret",
        "ACCESS_TOKEN": "your_access_token",
        "ACCOUNT_ID": "123456",
        "HOST": "demo"
      }
    }
  }
}
```

## Environment Variables

Instead of hardcoding credentials in the config, you can use your existing `.env` file:

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

This will use the `.env` file in the project directory.

## Testing the Configuration

After configuring, you can test by asking Claude:

- "Show me my cTrader account status"
- "List all available trading symbols"
- "What are my open positions?"

If properly configured, Claude will use the MCP tools to interact with your cTrader account.

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit credentials** to version control
2. **Use demo accounts** for testing
3. **Protect your config files** - they contain sensitive credentials
4. **Rotate access tokens** regularly
5. **Use read-only tokens** when possible for monitoring

## Troubleshooting

### Server not starting

Check the MCP server logs:
- Claude Desktop logs are usually in the app's log directory
- You can also run the server manually to see errors:
  ```bash
  python ctrader_mcp_server.py
  ```

### Authentication failures

- Verify credentials in `.env` or config
- Check that your cTrader account is active
- Ensure ACCESS_TOKEN is valid and not expired

### Tools not appearing

- Restart Claude Desktop completely
- Check config file syntax (valid JSON)
- Verify Python path is correct
- Ensure all dependencies are installed

## Advanced Configuration

### Multiple Accounts

You can configure multiple cTrader accounts:

```json
{
  "mcpServers": {
    "ctrader-demo": {
      "command": "python",
      "args": ["/path/to/ctrader_mcp_server.py"],
      "env": {
        "ACCOUNT_ID": "123456",
        "HOST": "demo"
      }
    },
    "ctrader-live": {
      "command": "python", 
      "args": ["/path/to/ctrader_mcp_server.py"],
      "env": {
        "ACCOUNT_ID": "789012",
        "HOST": "live"
      }
    }
  }
}
```

### Custom Configuration

You can add custom settings:

```json
{
  "mcpServers": {
    "ctrader": {
      "command": "python",
      "args": ["/path/to/ctrader_mcp_server.py"],
      "env": {
        "CLIENT_ID": "your_client_id",
        "CLIENT_SECRET": "your_client_secret",
        "ACCESS_TOKEN": "your_access_token",
        "ACCOUNT_ID": "123456",
        "HOST": "demo",
        "LOG_LEVEL": "DEBUG",
        "MAX_POSITIONS": "10"
      }
    }
  }
}
```

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)
- [cTrader API Documentation](https://help.ctrader.com/open-api/)
