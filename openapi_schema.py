#!/usr/bin/env python3
"""
OpenAPI schema generator for ChatGPT integration
Generates the schema that ChatGPT needs to understand your API
"""
import json
from fastapi.openapi.utils import get_openapi
from fastapi_server import app

def generate_chatgpt_schema():
    """Generate OpenAPI schema optimized for ChatGPT"""
    
    # Get the base OpenAPI schema
    schema = get_openapi(
        title="Kite Trading API",
        version="1.0.0",
        description="A comprehensive trading API for Zerodha Kite Connect integration. Supports buying/selling stocks, futures, options, and portfolio management.",
        routes=app.routes,
    )
    
    # Enhance descriptions for ChatGPT
    schema["info"]["description"] = """
    A comprehensive trading API for Indian stock markets via Zerodha Kite Connect.
    
    **Key Features:**
    - Buy/sell stocks, futures, options
    - Portfolio management
    - Real-time order execution
    - Comprehensive error handling
    
    **Supported Exchanges:**
    - NSE (National Stock Exchange)
    - NFO (NSE Futures & Options)
    - MCX (Multi Commodity Exchange)
    
    **Order Types:**
    - MARKET: Execute immediately at current market price
    - LIMIT: Execute only at specified price or better
    - SL: Stop Loss order
    - SL-M: Stop Loss Market order
    
    **Product Types:**
    - CNC: Cash and Carry (delivery)
    - MIS: Margin Intraday Square-off
    - NRML: Normal (for futures/options)
    """
    
    # Enhance endpoint descriptions
    if "paths" in schema:
        # Health check endpoint
        if "/" in schema["paths"] and "get" in schema["paths"]["/"]:
            schema["paths"]["/"]["get"]["description"] = "Check if the trading server is running and healthy"
            schema["paths"]["/"]["get"]["summary"] = "Health Check"
        
        # Authentication status
        if "/auth/status" in schema["paths"] and "get" in schema["paths"]["/auth/status"]:
            schema["paths"]["/auth/status"]["get"]["description"] = "Check if the user is authenticated with Kite Connect. Returns user information if authenticated."
            schema["paths"]["/auth/status"]["get"]["summary"] = "Check Authentication Status"
        
        # Buy endpoint
        if "/trade/buy" in schema["paths"] and "post" in schema["paths"]["/trade/buy"]:
            schema["paths"]["/trade/buy"]["post"]["description"] = """
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
            """
            schema["paths"]["/trade/buy"]["post"]["summary"] = "Buy Stocks/Futures/Options"
        
        # Sell endpoint
        if "/trade/sell" in schema["paths"] and "post" in schema["paths"]["/trade/sell"]:
            schema["paths"]["/trade/sell"]["post"]["description"] = """
            Place a SELL order for stocks, futures, or options.
            
            **Examples:**
            - Stock: {"stock": "TCS", "qty": 5}
            - Options: {"stock": "BANKNIFTY2561945000PE", "qty": 25, "exchange": "NFO"}
            
            **Important Notes:**
            - You must own the stock/position to sell
            - Market orders execute immediately at current price
            - Limit orders require a 'price' parameter
            """
            schema["paths"]["/trade/sell"]["post"]["summary"] = "Sell Stocks/Futures/Options"
        
        # Positions endpoint
        if "/trade/positions" in schema["paths"] and "get" in schema["paths"]["/trade/positions"]:
            schema["paths"]["/trade/positions"]["get"]["description"] = "Get current portfolio positions including stocks, futures, and options holdings"
            schema["paths"]["/trade/positions"]["get"]["summary"] = "Get Portfolio Positions"
    
    # Add examples to components
    if "components" in schema and "schemas" in schema["components"]:
        if "TradeRequest" in schema["components"]["schemas"]:
            schema["components"]["schemas"]["TradeRequest"]["examples"] = [
                {
                    "summary": "Buy Stock (Market Order)",
                    "value": {
                        "stock": "RELIANCE",
                        "qty": 10,
                        "exchange": "NSE",
                        "product": "CNC",
                        "order_type": "MARKET"
                    }
                },
                {
                    "summary": "Buy Stock (Limit Order)",
                    "value": {
                        "stock": "TCS",
                        "qty": 5,
                        "exchange": "NSE",
                        "product": "CNC",
                        "order_type": "LIMIT",
                        "price": 3500
                    }
                },
                {
                    "summary": "Buy Options (Intraday)",
                    "value": {
                        "stock": "NIFTY2561926000CE",
                        "qty": 75,
                        "exchange": "NFO",
                        "product": "MIS",
                        "order_type": "LIMIT",
                        "price": 1.5
                    }
                },
                {
                    "summary": "Buy Futures",
                    "value": {
                        "stock": "RELIANCE25JUNFUT",
                        "qty": 500,
                        "exchange": "NFO",
                        "product": "NRML",
                        "order_type": "MARKET"
                    }
                }
            ]
    
    # Add server information
    schema["servers"] = [
        {
            "url": "http://localhost:8080",
            "description": "Local development server"
        },
        {
            "url": "https://your-domain.com",
            "description": "Production server (replace with your actual domain)"
        }
    ]
    
    return schema

def save_schema_for_chatgpt():
    """Save the schema in a format suitable for ChatGPT"""
    schema = generate_chatgpt_schema()
    
    # Save full schema
    with open("openapi_schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    
    # Create a simplified version for ChatGPT
    chatgpt_schema = {
        "openapi": schema["openapi"],
        "info": schema["info"],
        "servers": schema["servers"],
        "paths": schema["paths"],
        "components": {
            "schemas": schema["components"]["schemas"]
        }
    }
    
    with open("chatgpt_schema.json", "w") as f:
        json.dump(chatgpt_schema, f, indent=2)
    
    print("✅ OpenAPI schemas generated:")
    print("   📄 openapi_schema.json - Full schema")
    print("   🤖 chatgpt_schema.json - ChatGPT optimized schema")
    
    return chatgpt_schema

if __name__ == "__main__":
    save_schema_for_chatgpt()
