# Kite Trading MCP Server (Python)

A Python MCP (Model Context Protocol) server for trading operations using the Kite Connect API, designed to work seamlessly with Claude Desktop.

## Features

- **Simple trading operations**: Buy, sell, and view portfolio
- **Real-time order execution**: Direct integration with Zerodha Kite Connect API
- **Text file logging**: All operations logged to `/app/logs/order.log`
- **Claude Desktop integration**: Works directly with Claude Desktop via MCP protocol

## Setup

### 🐳 Docker Deployment (Recommended)

1. **Clone and configure:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/kite-mcp-server2.git
   cd kite-mcp-server2
   cp .env.example .env
   # Edit .env with your Kite Connect credentials
   ```

2. **Start FastAPI server:**
   ```bash
   docker-compose up fastapi-server
   ```

3. **Access API:** http://localhost:8000/docs

📖 **Full Docker guide:** [README_Docker.md](README_Docker.md)

### 🐍 Local Python Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Kite Connect credentials
   ```

3. **Test environment setup:**
   ```bash
   python test_env.py
   ```

4. **One-time Authentication Setup:**
   ```bash
   python setup_auth.py
   ```
   This will:
   - Load credentials from .env file
   - Open your browser for Kite Connect login
   - Automatically handle the OAuth flow
   - Save your access token securely
   - Test the connection

5. **Run the servers:**
   ```bash
   python fastapi_server.py  # REST API server
   # OR
   python index.py          # MCP server for Claude Desktop
   ```

**Note:** You only need to authenticate once. The server will automatically:
- Use your saved access token
- Refresh tokens when they expire
- Handle re-authentication if needed

## Claude Desktop Integration

1. Create `claude_desktop_config.json` in:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

   With content:
   ```json
   {
     "mcpServers": {
       "trading-server": {
         "command": "python",
         "args": ["/path/to/your/kite-mcp-server2/index.py"],
         "env": {}
       }
     }
   }
   ```

   **Note**: Replace `/path/to/your/kite-mcp-server2/` with your actual project path.

2. Restart Claude Desktop

## Available Tools

- **`buy-a-stock`**: Buy stocks, futures, options, or any tradeable instrument
  - Required: `stock` (string), `qty` (number)
  - Optional: `exchange` (NSE/NFO/MCX), `product` (CNC/MIS/NRML), `order_type` (MARKET/LIMIT/SL/SL-M), `price`, `trigger_price`
  - Examples:
    - Stock: `{"stock": "RELIANCE", "qty": 10}`
    - Options: `{"stock": "NIFTY2561926000CE", "qty": 75, "exchange": "NFO", "product": "MIS", "order_type": "LIMIT", "price": 1.5}`
    - Futures: `{"stock": "RELIANCE25JUNFUT", "qty": 500, "exchange": "NFO", "product": "NRML"}`

- **`sell-a-stock`**: Sell stocks, futures, options, or any tradeable instrument
  - Required: `stock` (string), `qty` (number)
  - Optional: `exchange` (NSE/NFO/MCX), `product` (CNC/MIS/NRML), `order_type` (MARKET/LIMIT/SL/SL-M), `price`, `trigger_price`
  - Examples:
    - Stock: `{"stock": "TCS", "qty": 5}`
    - Options: `{"stock": "BANKNIFTY2561945000PE", "qty": 25, "exchange": "NFO", "product": "MIS", "order_type": "LIMIT", "price": 50}`

- **`show-portfolio`**: Show current portfolio positions
  - Parameters: None

## Usage Examples

In Claude Desktop, you can say:

**Stocks:**
- "Buy 10 shares of Reliance"
- "Sell 5 shares of TCS at limit price 3500"
- "Buy 100 shares of INFY for delivery"

**Options:**
- "Buy 75 NIFTY 26000 CE options at 1.5"
- "Sell 25 BANKNIFTY 45000 PE options at 50"
- "Buy NIFTY options expiring June 19th, strike 26000 CE, quantity 75, limit price 1.5"

**Futures:**
- "Buy 500 Reliance June futures"
- "Buy 50 NIFTY June futures"
- "Sell 15 BANKNIFTY June futures"

**Advanced Orders:**
- "Buy 50 shares of HDFC with stop loss at 1500"
- "Sell 100 shares of ICICI with limit order at 950"

Claude will automatically use the trading tools with appropriate parameters for each order type.

## File Structure

### Core Files
- `index.py`: Main MCP server implementation
- `fastapi_server.py`: FastAPI REST server implementation
- `trade.py`: Trading operations using Kite Connect API
- `auth.py`: Automated OAuth authentication
- `logger.py`: Simple text file logging

### Setup & Configuration
- `setup_auth.py`: One-time authentication setup
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (API credentials)
- `.env.example`: Environment template

### Testing & Examples
- `test_env.py`: Environment variable testing
- `test_trade.py`: MCP server testing
- `client_example.py`: FastAPI client example

### Docker & Deployment
- `Dockerfile`: Container configuration
- `docker-compose.yml`: Multi-service orchestration
- `docker-entrypoint.sh`: Container startup script

### Documentation
- `README.md`: Main documentation
- `README_Docker.md`: Docker deployment guide
- `README_FastAPI.md`: FastAPI documentation
- `DEPLOYMENT_GUIDE.md`: Complete deployment guide

### Auto-generated Files
- `/app/data/kite_session.json`: Saved session data (auto-created)
- `/app/logs/order.log`: Trading operations log (auto-created)

## Enhanced Logging

All trading operations are logged to `/app/logs/order.log` with detailed information:
```
2024-01-01T12:00:00 | BUY | RELIANCE | Qty: 10 | NSE | CNC | MARKET
2024-01-01T12:01:00 | SELL | TCS | Qty: 5 | NSE | CNC | LIMIT | Price: 3500
```

## Security Notes

- Session data is saved locally for continuous trading
- Never share your API credentials or session files
- All operations are logged for audit purposes

## Troubleshooting

1. **"Invalid access token"**: Run `python setup_auth.py` to re-authenticate
2. **"Module not found"**: Run `pip install -r requirements.txt`
3. **"Connection refused"**: Ensure Kite Connect API is accessible

## Converting from JavaScript

This Python server is equivalent to the JavaScript version with the same functionality:
- Same tool names and descriptions
- Same input/output formats
- Same MCP protocol compliance
- Compatible with Claude Desktop
