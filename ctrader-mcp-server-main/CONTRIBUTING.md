# Contributing to cTrader MCP Server

Thank you for your interest in contributing to the cTrader MCP Server! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

1. **Clear title** - Describe the bug briefly
2. **Steps to reproduce** - How to trigger the bug
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happens
5. **Environment** - OS, Python version, cTrader account type
6. **Logs** - Any relevant error messages

Example:
```
Title: Market order fails with EURUSD

Steps to reproduce:
1. Call create_market_order with symbol "EURUSD"
2. Volume 0.01, side "BUY"

Expected: Order should be created
Actual: Error "Symbol not found"

Environment: Ubuntu 22.04, Python 3.10, Demo account
```

### Suggesting Features

For feature requests, create an issue with:

1. **Use case** - Why is this feature needed?
2. **Description** - What should it do?
3. **Examples** - How would it be used?
4. **Alternatives** - Other ways to achieve the goal?

### Pull Requests

1. **Fork the repository**
2. **Create a branch** - `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test thoroughly** - Ensure nothing breaks
5. **Commit with clear messages**
6. **Push to your fork**
7. **Create a pull request**

#### Pull Request Guidelines

- One feature/fix per PR
- Clear description of changes
- Update documentation if needed
- Add tests for new features
- Follow the existing code style
- Ensure all tests pass

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/ctrader-mcp-server.git
cd ctrader-mcp-server

# Install in development mode
./install.sh

# Activate virtual environment
source venv/bin/activate

# Run tests
python test_server.py
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use docstrings for functions and classes
- Type hints are encouraged

Example:
```python
def create_order(
    symbol: str,
    side: str,
    volume: float,
    stop_loss: Optional[float] = None
) -> dict:
    """
    Create a trading order.
    
    Args:
        symbol: Trading symbol (e.g., "EURUSD")
        side: Order side ("BUY" or "SELL")
        volume: Volume in lots
        stop_loss: Optional stop loss price
        
    Returns:
        Dictionary with order details
    """
    # Implementation here
    pass
```

### Documentation Style

- Use Markdown for documentation
- Include code examples
- Keep explanations clear and concise
- Update relevant docs when changing code

## Testing

### Before Submitting

1. **Run the test suite**
   ```bash
   python test_server.py
   ```

2. **Test on demo account** - Never test on live

3. **Check different scenarios**
   - Valid inputs
   - Invalid inputs
   - Edge cases
   - Error handling

### Adding Tests

When adding new features, include tests:

```python
async def test_new_feature():
    """Test the new feature works correctly"""
    server = CTraderMCPServer()
    await server.initialize_bot()
    
    result = await server._execute_tool("new_tool", {"param": "value"})
    
    assert result["success"] == True
    assert "expected_field" in result
```

## Adding New Tools

To add a new tool to the MCP server:

### 1. Add Tool Definition

In `server.py`, add to `handle_list_tools()`:

```python
types.Tool(
    name="your_tool_name",
    description="What the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "First parameter"
            }
        },
        "required": ["param1"]
    }
)
```

### 2. Implement Handler

In `server.py`, add to `_execute_tool()`:

```python
elif name == "your_tool_name":
    param1 = arguments["param1"]
    
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        self.bot.your_method,
        param1
    )
    
    return {
        "success": True,
        "data": result
    }
```

### 3. Add Bot Method (if needed)

In `ctrader_bot.py`:

```python
def your_method(self, param1: str) -> dict:
    """
    Your method implementation.
    
    Args:
        param1: Description
        
    Returns:
        Result dictionary
    """
    if not self.is_account_authenticated:
        print("✗ Not authenticated")
        return None
    
    # Implementation
    return {"result": "value"}
```

### 4. Update Documentation

- Add to `docs/API.md`
- Update `README.md` if needed
- Add examples to `docs/GUIDE.md`

### 5. Add Tests

In `test_server.py`:

```python
# Test your new tool
result = await server._execute_tool("your_tool_name", {"param1": "test"})
assert result.get("success") == True
```

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: Add trailing stop-loss support
fix: Handle connection timeout errors
docs: Update API reference for new tools
test: Add tests for order modification
refactor: Simplify error handling logic
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

## Release Process

1. Update `CHANGELOG.md`
2. Update version number
3. Create git tag
4. Push to repository
5. Create GitHub release

## Questions?

- Check existing issues
- Read the documentation
- Ask in discussions
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be acknowledged in the project README and release notes.

---

Thank you for contributing to cTrader MCP Server! 🚀
