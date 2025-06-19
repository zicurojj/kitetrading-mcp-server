from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Union, Optional
import uvicorn
import os
from auth import is_authenticated, get_session_info, clear_session, get_valid_access_token
from trade import place_order, get_positions

app = FastAPI()

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

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/auth/status")
def auth_status():
    if is_authenticated():
        return {"authenticated": True, "session": get_session_info()}
    return {"authenticated": False}

@app.post("/auth/logout")
def auth_logout():
    cleared = clear_session()
    return {"cleared": cleared}

@app.post("/trade/buy")
async def trade_buy(req: TradeRequest, _: None = Depends(verify_auth)):
    result = await place_order(req.stock, req.qty, transaction_type="BUY", exchange=req.exchange,
                               product=req.product, order_type=req.order_type, price=req.price,
                               trigger_price=req.trigger_price, variety=req.variety, validity=req.validity)

    # Handle both success and error responses consistently
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Order failed"))

    return result

@app.post("/trade/sell")
async def trade_sell(req: TradeRequest, _: None = Depends(verify_auth)):
    result = await place_order(req.stock, req.qty, transaction_type="SELL", exchange=req.exchange,
                               product=req.product, order_type=req.order_type, price=req.price,
                               trigger_price=req.trigger_price, variety=req.variety, validity=req.validity)

    # Handle both success and error responses consistently
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Order failed"))

    return result

@app.get("/trade/positions")
async def trade_positions(_: None = Depends(verify_auth)):
    return {"positions": await get_positions()}

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
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
        print("💡 Make sure port 8000 is not already in use")
