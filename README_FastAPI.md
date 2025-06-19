# Kite Trading FastAPI Server

A modern REST API server for trading operations using Zerodha Kite Connect API, built with FastAPI.

## 🚀 Features

- **REST API**: Clean HTTP endpoints for all trading operations
- **Interactive Documentation**: Auto-generated API docs with Swagger UI
- **Authentication Management**: Simple session-based auth with Kite Connect
- **Real-time Trading**: Direct integration with Zerodha Kite Connect API
- **Comprehensive Logging**: All operations logged to `order2.log`
- **CORS Support**: Ready for web frontend integration
- **Type Safety**: Full Pydantic validation for all requests/responses

## 📦 Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **One-time Authentication Setup:**
   ```bash
   python setup_auth.py
   ```
   - Opens browser for Kite Connect login
   - Enter your credentials + mobile app OTP
   - System automatically saves session for continuous trading

## 🏃‍♂️ Running the Server

```bash
python fastapi_server.py
```

The server will start on `http://localhost:8000`

**Available URLs:**
- 📖 **API Documentation**: http://localhost:8000/docs
- 🔧 **Alternative Docs**: http://localhost:8000/redoc  
- 💚 **Health Check**: http://localhost:8000/

## 📚 API Endpoints

### Authentication
- `GET /auth/status` - Check authentication status
- `POST /auth/logout` - Clear saved session

### Trading
- `POST /trade/buy` - Buy stocks/futures/options
- `POST /trade/sell` - Sell stocks/futures/options  
- `GET /trade/positions` - Get current portfolio

### System
- `GET /` - Health check

## 🔧 API Usage Examples

### 1. Check Server Health
```bash
curl http://localhost:8000/
```

### 2. Check Authentication Status
```bash
curl http://localhost:8000/auth/status
```

### 3. Buy Stock (Market Order)
```bash
curl -X POST http://localhost:8000/trade/buy \
  -H "Content-Type: application/json" \
  -d '{
    "stock": "RELIANCE",
    "qty": 1,
    "exchange": "NSE",
    "product": "CNC",
    "order_type": "MARKET"
  }'
```

### 4. Buy Stock (Limit Order)
```bash
curl -X POST http://localhost:8000/trade/buy \
  -H "Content-Type: application/json" \
  -d '{
    "stock": "TCS",
    "qty": 10,
    "exchange": "NSE",
    "product": "CNC", 
    "order_type": "LIMIT",
    "price": 3500
  }'
```

### 5. Buy NIFTY Options (Intraday)
```bash
curl -X POST http://localhost:8000/trade/buy \
  -H "Content-Type: application/json" \
  -d '{
    "stock": "NIFTY2561926000CE",
    "qty": 75,
    "exchange": "NFO",
    "product": "MIS",
    "order_type": "MARKET"
  }'
```

### 6. Get Portfolio Positions
```bash
curl http://localhost:8000/trade/positions
```

## 🐍 Python Client Usage

```python
from client_example import KiteTradingClient

# Initialize client
client = KiteTradingClient("http://localhost:8000")

# Check server health
health = client.health_check()
print(health)

# Check authentication
auth = client.auth_status()
print(auth)

# Buy stock
result = client.buy_stock("RELIANCE", 1)
print(result)

# Buy with limit price
result = client.buy_stock("TCS", 10, order_type="LIMIT", price=3500)
print(result)

# Get positions
positions = client.get_positions()
print(positions)
```

## 🧪 Testing

Run the test suite:
```bash
python test_fastapi.py
```

Run the client example:
```bash
python client_example.py
```

## 📊 Request/Response Format

### Buy/Sell Request
```json
{
  "stock": "RELIANCE",
  "qty": 1,
  "exchange": "NSE",
  "product": "CNC",
  "order_type": "MARKET",
  "price": null,
  "trigger_price": null,
  "variety": "regular",
  "validity": "DAY"
}
```

### Order Response
```json
{
  "success": true,
  "message": "BUY order placed: 1 units of RELIANCE",
  "order_id": "240101000000001",
  "details": {
    "stock": "RELIANCE",
    "quantity": 1,
    "transaction_type": "BUY",
    "exchange": "NSE",
    "product": "CNC",
    "order_type": "MARKET"
  }
}
```

## 🔒 Security Notes

- Session data is saved locally in `/app/data/kite_session.json`
- Never share your API credentials or session files
- All operations are logged for audit purposes
- Configure CORS origins for production use

## 🛠️ Development

The FastAPI server provides:
- **Auto-reload**: Changes are automatically detected
- **Type hints**: Full Python type safety
- **Validation**: Automatic request/response validation
- **Documentation**: Interactive API docs
- **Testing**: Built-in test client support

## 🔄 Migration from MCP

If you were using the MCP version (`index.py`), the FastAPI version provides the same functionality through REST endpoints:

- `buy-a-stock` tool → `POST /trade/buy`
- `sell-a-stock` tool → `POST /trade/sell`  
- `show-portfolio` tool → `GET /trade/positions`

## 📁 File Structure

- `fastapi_server.py` - Main FastAPI application
- `client_example.py` - Python client example
- `test_fastapi.py` - Test suite
- `auth.py` - Authentication system (shared)
- `trade.py` - Trading functions (shared)
- `setup_auth.py` - One-time auth setup (shared)

## 🚨 Troubleshooting

1. **Server won't start**: Check if port 8000 is available
2. **Authentication failed**: Run `python setup_auth.py`
3. **Orders failing**: Verify authentication status via `/auth/status`
4. **CORS issues**: Update CORS settings in `fastapi_server.py`

---

🎉 **Ready to trade with FastAPI!** Visit http://localhost:8000/docs for interactive API documentation.
