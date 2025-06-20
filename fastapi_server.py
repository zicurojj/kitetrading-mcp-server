from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union, Optional
import uvicorn
import os
from docker_auth import is_authenticated, get_session_info, clear_session, get_valid_access_token
from trade import place_order, get_positions

# Create FastAPI app with enhanced metadata for ChatGPT
app = FastAPI(
    title="Kite Trading API",
    description="A comprehensive trading API for Indian stock markets via Zerodha Kite Connect",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for ChatGPT integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify ChatGPT's domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TradeRequest(BaseModel):
    stock: str
    qty: int
    exchange: str = "NSE"
    product: str = "CNC"
    order_type: str = "MARKET"
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    variety: str = "regular"
    validity: str = "DAY"

def verify_auth():
    if not is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/",
         summary="Health Check",
         description="Check if the trading server is running and healthy",
         tags=["System"])
def root():
    return {"status": "running", "message": "Kite Trading API is operational"}

@app.get("/auth/status",
         summary="Check Authentication Status",
         description="Check if the user is authenticated with Kite Connect. Returns user information if authenticated.",
         tags=["Authentication"])
def auth_status():
    if is_authenticated():
        return {"authenticated": True, "session": get_session_info()}
    return {"authenticated": False, "message": "Not authenticated. Please authenticate first."}

@app.post("/auth/logout",
          summary="Logout",
          description="Clear the saved authentication session",
          tags=["Authentication"])
def auth_logout():
    cleared = clear_session()
    return {"cleared": cleared, "message": "Session cleared successfully" if cleared else "No session to clear"}

@app.post("/trade/buy",
          summary="Buy Stocks/Futures/Options",
          description="""
          Place a BUY order for stocks, futures, or options.

          **Examples:**
          - Stock: {"stock": "RELIANCE", "qty": 10}
          - Options: {"stock": "NIFTY2561926000CE", "qty": 75, "exchange": "NFO", "product": "MIS"}
          - Futures: {"stock": "RELIANCE25JUNFUT", "qty": 500, "exchange": "NFO"}

          **Important Notes:**
          - Market orders execute immediately at current price
          - Limit orders require a 'price' parameter
          - Options/Futures require 'exchange': 'NFO'
          - For intraday trading, use 'product': 'MIS'
          """,
          tags=["Trading"])
async def trade_buy(req: TradeRequest, _: None = Depends(verify_auth)):
    result = await place_order(req.stock, req.qty, transaction_type="BUY", exchange=req.exchange,
                               product=req.product, order_type=req.order_type, price=req.price,
                               trigger_price=req.trigger_price, variety=req.variety, validity=req.validity)

    # Handle both success and error responses consistently
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Order failed"))

    return result

@app.post("/trade/sell",
          summary="Sell Stocks/Futures/Options",
          description="""
          Place a SELL order for stocks, futures, or options.

          **Examples:**
          - Stock: {"stock": "TCS", "qty": 5}
          - Options: {"stock": "BANKNIFTY2561945000PE", "qty": 25, "exchange": "NFO"}

          **Important Notes:**
          - You must own the stock/position to sell
          - Market orders execute immediately at current price
          - Limit orders require a 'price' parameter
          """,
          tags=["Trading"])
async def trade_sell(req: TradeRequest, _: None = Depends(verify_auth)):
    result = await place_order(req.stock, req.qty, transaction_type="SELL", exchange=req.exchange,
                               product=req.product, order_type=req.order_type, price=req.price,
                               trigger_price=req.trigger_price, variety=req.variety, validity=req.validity)

    # Handle both success and error responses consistently
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Order failed"))

    return result

@app.get("/trade/positions",
         summary="Get Portfolio Positions",
         description="Get current portfolio positions including stocks, futures, and options holdings",
         tags=["Trading"])
async def trade_positions(_: None = Depends(verify_auth)):
    return {"positions": await get_positions()}

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8080"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    reload = os.getenv("RELOAD", "false").lower() == "true"

    print("🚀 Starting Kite Trading FastAPI Server...")
    print(f"📡 Server: http://{host}:{port}")
    print(f"📖 API Docs: http://{host}:{port}/docs")
    print(f"🔧 Debug mode: {debug}")

    try:
        uvicorn.run(
            "fastapi_server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info" if not debug else "debug"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        print(f"💡 Make sure port {port} is not already in use")
