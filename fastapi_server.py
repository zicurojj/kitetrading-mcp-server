#!/usr/bin/env python3
"""
FastAPI Trading Server for Kite Connect
Simple REST API for trading operations using Zerodha Kite Connect
"""

import os
import sys
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Please install it with: pip install python-dotenv", file=sys.stderr)
    print("Falling back to system environment variables only.", file=sys.stderr)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn

# Import our trading functions
from trade import place_order, get_positions
from auth import get_valid_access_token, is_authenticated, get_session_info, clear_session

# FastAPI app
app = FastAPI(
    title="Kite Trading API",
    description="REST API for trading operations using Zerodha Kite Connect",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class BuyStockRequest(BaseModel):
    stock: str = Field(..., description="Stock symbol (e.g., RELIANCE, NIFTY2561926000CE)")
    qty: int = Field(..., description="Quantity to buy")
    exchange: str = Field("NSE", description="Exchange (NSE, NFO, MCX, etc.)")
    product: str = Field("CNC", description="Product type (CNC, MIS, NRML)")
    order_type: str = Field("MARKET", description="Order type (MARKET, LIMIT, SL, SL-M)")
    price: Optional[float] = Field(None, description="Price for LIMIT orders")
    trigger_price: Optional[float] = Field(None, description="Trigger price for SL orders")
    variety: str = Field("regular", description="Order variety (regular, amo, co, iceberg)")
    validity: str = Field("DAY", description="Order validity (DAY, IOC)")

class SellStockRequest(BaseModel):
    stock: str = Field(..., description="Stock symbol (e.g., RELIANCE, NIFTY2561926000CE)")
    qty: int = Field(..., description="Quantity to sell")
    exchange: str = Field("NSE", description="Exchange (NSE, NFO, MCX, etc.)")
    product: str = Field("CNC", description="Product type (CNC, MIS, NRML)")
    order_type: str = Field("MARKET", description="Order type (MARKET, LIMIT, SL, SL-M)")
    price: Optional[float] = Field(None, description="Price for LIMIT orders")
    trigger_price: Optional[float] = Field(None, description="Trigger price for SL orders")
    variety: str = Field("regular", description="Order variety (regular, amo, co, iceberg)")
    validity: str = Field("DAY", description="Order validity (DAY, IOC)")

class OrderResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PositionsResponse(BaseModel):
    success: bool
    message: str
    positions: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_info: Optional[Dict[str, Any]] = None

# Dependency to check authentication
async def verify_auth():
    """Verify that user is authenticated"""
    if not is_authenticated():
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Please run setup_auth.py first or call /auth/login"
        )
    return True

# Health check endpoint
@app.get("/", response_model=Dict[str, str])
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Kite Trading API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Authentication endpoints
@app.get("/auth/status", response_model=AuthResponse)
async def auth_status():
    """Check authentication status"""
    try:
        if is_authenticated():
            info = get_session_info()
            return AuthResponse(
                success=True,
                message="Authenticated",
                user_info=info
            )
        else:
            return AuthResponse(
                success=False,
                message="Not authenticated. Please run setup_auth.py first."
            )
    except Exception as e:
        return AuthResponse(
            success=False,
            message=f"Error checking auth status: {str(e)}"
        )

@app.post("/auth/login", response_model=AuthResponse)
async def login():
    """Trigger authentication flow (requires manual setup_auth.py for now)"""
    return AuthResponse(
        success=False,
        message="Please run 'python setup_auth.py' from command line for initial authentication"
    )

@app.post("/auth/logout", response_model=AuthResponse)
async def logout():
    """Clear saved session"""
    try:
        if clear_session():
            return AuthResponse(
                success=True,
                message="Session cleared successfully"
            )
        else:
            return AuthResponse(
                success=False,
                message="No session found to clear"
            )
    except Exception as e:
        return AuthResponse(
            success=False,
            message=f"Error clearing session: {str(e)}"
        )

# Trading endpoints
@app.post("/trade/buy", response_model=OrderResponse, dependencies=[Depends(verify_auth)])
async def buy_stock(request: BuyStockRequest):
    """Buy stocks, futures, options, or any tradeable instrument"""
    try:
        result = await place_order(
            tradingsymbol=request.stock,
            quantity=request.qty,
            transaction_type="BUY",
            exchange=request.exchange,
            product=request.product,
            order_type=request.order_type,
            price=request.price,
            trigger_price=request.trigger_price,
            variety=request.variety,
            validity=request.validity
        )

        # Extract order ID
        order_id = "N/A"
        if isinstance(result, dict):
            order_id = result.get('order_id', 'N/A')
        elif isinstance(result, str):
            order_id = result

        # Create detailed message
        order_details = f"{request.qty} units of {request.stock}"
        if request.price:
            order_details += f" at ₹{request.price}"
        if request.order_type != "MARKET":
            order_details += f" ({request.order_type})"

        return OrderResponse(
            success=True,
            message=f"BUY order placed: {order_details}",
            order_id=order_id,
            details={
                "stock": request.stock,
                "quantity": request.qty,
                "transaction_type": "BUY",
                "exchange": request.exchange,
                "product": request.product,
                "order_type": request.order_type,
                "price": request.price,
                "trigger_price": request.trigger_price
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to buy {request.stock}: {str(e)}"
        )

@app.post("/trade/sell", response_model=OrderResponse, dependencies=[Depends(verify_auth)])
async def sell_stock(request: SellStockRequest):
    """Sell stocks, futures, options, or any tradeable instrument"""
    try:
        result = await place_order(
            tradingsymbol=request.stock,
            quantity=request.qty,
            transaction_type="SELL",
            exchange=request.exchange,
            product=request.product,
            order_type=request.order_type,
            price=request.price,
            trigger_price=request.trigger_price,
            variety=request.variety,
            validity=request.validity
        )

        # Extract order ID
        order_id = "N/A"
        if isinstance(result, dict):
            order_id = result.get('order_id', 'N/A')
        elif isinstance(result, str):
            order_id = result

        # Create detailed message
        order_details = f"{request.qty} units of {request.stock}"
        if request.price:
            order_details += f" at ₹{request.price}"
        if request.order_type != "MARKET":
            order_details += f" ({request.order_type})"

        return OrderResponse(
            success=True,
            message=f"SELL order placed: {order_details}",
            order_id=order_id,
            details={
                "stock": request.stock,
                "quantity": request.qty,
                "transaction_type": "SELL",
                "exchange": request.exchange,
                "product": request.product,
                "order_type": request.order_type,
                "price": request.price,
                "trigger_price": request.trigger_price
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to sell {request.stock}: {str(e)}"
        )

@app.get("/trade/positions", response_model=PositionsResponse, dependencies=[Depends(verify_auth)])
async def get_portfolio():
    """Get current portfolio positions"""
    try:
        positions = await get_positions()
        return PositionsResponse(
            success=True,
            message="Portfolio retrieved successfully",
            positions=positions
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch portfolio: {str(e)}"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    print("🚀 Starting Kite Trading FastAPI Server...")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Alternative docs: http://{host}:{port}/redoc")
    print(f"💡 Health check: http://{host}:{port}/")
    print(f"⚙️  Configuration: Host={host}, Port={port}, Reload={reload}")

    uvicorn.run(
        "fastapi_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )
