import asyncio
import json
import sys
import os
from typing import Any, Dict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Please install it with: pip install python-dotenv", file=sys.stderr)
    print("Falling back to system environment variables only.", file=sys.stderr)

# Try to import pydantic, provide fallback if not available
try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    print("Warning: pydantic not found. Please install it with: pip install pydantic", file=sys.stderr)
    # Simple fallback BaseModel
    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)
        
        @classmethod
        def parse_obj(cls, obj):
            return cls(**obj)
        
        @classmethod
        def model_validate(cls, obj):
            return cls(**obj)
        
        @classmethod
        def schema(cls):
            return {"properties": {}, "required": []}
        
        @classmethod
        def model_json_schema(cls):
            return {"properties": {}, "required": []}
    
    class ValidationError(Exception):
        def __init__(self, message):
            self.message = message
        
        def errors(self):
            return [{"msg": self.message}]

from trade import place_order, get_positions

# Input schemas
class BuyStockInput(BaseModel):
    stock: str
    qty: int
    exchange: str = "NSE"  # NSE, NFO, MCX, etc.
    product: str = "CNC"   # CNC, MIS, NRML
    order_type: str = "MARKET"  # MARKET, LIMIT, SL, SL-M
    price: float = None
    trigger_price: float = None

class SellStockInput(BaseModel):
    stock: str
    qty: int
    exchange: str = "NSE"  # NSE, NFO, MCX, etc.
    product: str = "CNC"   # CNC, MIS, NRML
    order_type: str = "MARKET"  # MARKET, LIMIT, SL, SL-M
    price: float = None
    trigger_price: float = None

class EmptyInput(BaseModel):
    pass

# MCP Server implementation
class McpServer:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    def add_tool(self, name: str, description: str, schema: BaseModel, func):
        """Add a tool to the server"""
        # Convert Pydantic schema to JSON schema
        try:
            # Try the new method first (Pydantic V2)
            json_schema = schema.model_json_schema()
        except AttributeError:
            # Fallback to old method (Pydantic V1 or our mock)
            try:
                json_schema = schema.schema()
            except AttributeError:
                # Ultimate fallback for our mock BaseModel
                json_schema = {"properties": {}, "required": []}

        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": json_schema.get("properties", {}),
                "required": json_schema.get("required", [])
            },
            "handler": func,
            "schema": schema
        }

    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request"""
        _ = params  # Acknowledge parameter
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }

    async def handle_tools_list(self, params: Dict) -> Dict:
        """Handle tools/list request"""
        _ = params  # Acknowledge parameter
        tools_list = []
        for tool_name, tool_info in self.tools.items():
            tools_list.append({
                "name": tool_info["name"],
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"]
            })
        
        return {"tools": tools_list}

    async def handle_tools_call(self, params: Dict) -> Dict:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_info = self.tools[tool_name]
        handler = tool_info["handler"]
        schema = tool_info["schema"]
        
        try:
            # Validate input using Pydantic schema
            try:
                # Try Pydantic V2 method first
                validated_input = schema.model_validate(arguments)
            except AttributeError:
                # Fallback to V1 method or our mock
                validated_input = schema.parse_obj(arguments)
            
            result = await handler(validated_input)
            
            # Ensure result has proper MCP format
            if not isinstance(result, dict) or "content" not in result:
                # Convert simple results to proper MCP format
                if isinstance(result, str):
                    result = {"content": [{"type": "text", "text": result}]}
                elif isinstance(result, dict) and "error" in result:
                    result = {
                        "content": [{"type": "text", "text": result["error"]}],
                        "isError": True
                    }
            
            return result
            
        except ValidationError as e:
            return {
                "content": [{"type": "text", "text": f"Invalid input: {e.errors()}"}],
                "isError": True
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }

    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            response = {
                "jsonrpc": "2.0",
                "result": result
            }
            # Only include id if it's not None
            if request_id is not None:
                response["id"] = request_id
            return response
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            # Only include id if it's not None
            if request_id is not None:
                error_response["id"] = request_id
            return error_response

    async def run(self):
        """Run the MCP server"""
        print(f"MCP Server '{self.name}' v{self.version} starting...", file=sys.stderr)
        
        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, input)
                if not line.strip():
                    continue
                
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                
                # Validate basic JSON-RPC structure
                if not isinstance(request, dict):
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Invalid Request"}
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                
                # Get request ID early for proper error responses
                request_id = request.get("id")
                
                if request.get("jsonrpc") != "2.0":
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Invalid JSON-RPC version"}
                    }
                    if request_id is not None:
                        error_response["id"] = request_id
                    print(json.dumps(error_response), flush=True)
                    continue
                
                # Validate required method field
                if "method" not in request:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Missing method field"}
                    }
                    if request_id is not None:
                        error_response["id"] = request_id
                    print(json.dumps(error_response), flush=True)
                    continue
                
                # Handle the request
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
                
            except EOFError:
                # Client disconnected
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                }
                print(json.dumps(error_response), flush=True)

# Tool implementations for Claude Desktop
async def buy_stock(data: BuyStockInput):
    """Buy stocks, futures, options, or any tradeable instrument"""
    try:
        result = await place_order(
            tradingsymbol=data.stock,
            quantity=data.qty,
            transaction_type="BUY",
            exchange=data.exchange,
            product=data.product,
            order_type=data.order_type,
            price=data.price,
            trigger_price=data.trigger_price
        )

        # Create detailed response message
        order_details = f"{data.qty} units of {data.stock}"
        if data.price:
            order_details += f" at ₹{data.price}"
        if data.order_type != "MARKET":
            order_details += f" ({data.order_type})"

        # Handle different response formats
        order_id = "N/A"
        if isinstance(result, dict):
            order_id = result.get('order_id', 'N/A')
        elif isinstance(result, str):
            order_id = result

        return {
            "content": [{"type": "text", "text": f"✅ BUY order placed: {order_details}\n📋 Order ID: {order_id}\n🏢 Exchange: {data.exchange} | Product: {data.product}"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Failed to buy {data.stock}: {str(e)}"}],
            "isError": True
        }

async def sell_stock(data: SellStockInput):
    """Sell stocks, futures, options, or any tradeable instrument"""
    try:
        result = await place_order(
            tradingsymbol=data.stock,
            quantity=data.qty,
            transaction_type="SELL",
            exchange=data.exchange,
            product=data.product,
            order_type=data.order_type,
            price=data.price,
            trigger_price=data.trigger_price
        )

        # Create detailed response message
        order_details = f"{data.qty} units of {data.stock}"
        if data.price:
            order_details += f" at ₹{data.price}"
        if data.order_type != "MARKET":
            order_details += f" ({data.order_type})"

        # Handle different response formats
        order_id = "N/A"
        if isinstance(result, dict):
            order_id = result.get('order_id', 'N/A')
        elif isinstance(result, str):
            order_id = result

        return {
            "content": [{"type": "text", "text": f"✅ SELL order placed: {order_details}\n📋 Order ID: {order_id}\n🏢 Exchange: {data.exchange} | Product: {data.product}"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Failed to sell {data.stock}: {str(e)}"}],
            "isError": True
        }

async def show_portfolio(_: EmptyInput):
    """Show current portfolio positions"""
    try:
        holdings = await get_positions()
        return {
            "content": [{"type": "text", "text": f"Current Portfolio:\n{holdings}"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Failed to fetch portfolio: {str(e)}"}],
            "isError": True
        }

def main():
    """Main function to start the MCP server for Claude Desktop"""
    server = McpServer(name="Trading Server", version="1.0.0")

    # Add trading tools for Claude Desktop
    server.add_tool(
        "buy-a-stock",
        "Buy stocks, futures, options, or any tradeable instrument. Supports all exchanges (NSE, NFO, MCX) and order types (MARKET, LIMIT, SL, SL-M). Requires stock symbol and quantity. Optional: exchange, product, order_type, price, trigger_price.",
        BuyStockInput,
        buy_stock
    )
    server.add_tool(
        "sell-a-stock",
        "Sell stocks, futures, options, or any tradeable instrument. Supports all exchanges (NSE, NFO, MCX) and order types (MARKET, LIMIT, SL, SL-M). Requires stock symbol and quantity. Optional: exchange, product, order_type, price, trigger_price.",
        SellStockInput,
        sell_stock
    )
    server.add_tool(
        "show-portfolio",
        "Show current portfolio positions",
        EmptyInput,
        show_portfolio
    )

    # Start the server
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
