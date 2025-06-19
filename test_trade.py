#!/usr/bin/env python3
"""
Test MCP Server Tools with Automated Auth
"""

import asyncio
import sys
import os



# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Test different order types using MCP tools with automated auth"""
    try:
        print("🎯 Testing MCP Server with Automated Auth")
        print("=" * 50)

        # Test auth first
        print("🔐 Testing authentication...")
        from auth import get_valid_access_token
        token = get_valid_access_token()
        if token:
            print(f"✅ Auth successful! Token: {token[:10]}...")
        else:
            print("❌ Auth failed!")
            return

        from index import buy_stock, sell_stock, show_portfolio, BuyStockInput, SellStockInput, EmptyInput

        # Test 1: Show Portfolio
        print("\n1️⃣ Show Portfolio:")
        portfolio_result = await show_portfolio(EmptyInput())

        # Extract and display portfolio data properly
        if 'content' in portfolio_result and len(portfolio_result['content']) > 0:
            portfolio_text = portfolio_result['content'][0]['text']
            print("📊 Portfolio:")
            print("=" * 50)

            # Split the text and format it nicely
            lines = portfolio_text.split('\n')
            for line in lines:
                if line.strip():
                    if line.startswith('Current Portfolio:'):
                        print(f"💼 {line}")
                    elif 'stock:' in line:
                        # Parse the stock line
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            stock = parts[0].replace('stock: ', '')
                            qty = parts[1].replace('qty: ', '')
                            price = parts[2].replace('currentPrice: ', '')

                            # Format with emojis and better spacing
                            if float(qty) > 0:
                                print(f"📈 {stock:<20} | Qty: {qty:>8} | Price: ₹{price}")
                            else:
                                print(f"📊 {stock:<20} | Qty: {qty:>8} | Price: ₹{price} (No position)")
            print("=" * 50)
        else:
            print(f"📊 Raw Portfolio Data: {portfolio_result}")

        # Test 2: Buy 2 shares of GTLINFRA
        print("\n2️⃣ Buying 2 shares of GTLINFRA:")
        buy_input = BuyStockInput(
            stock="GTLINFRA",
            qty=2,
            exchange="NSE",
            product="CNC",
            order_type="MARKET"
        )
        result = await buy_stock(buy_input)
        print(f"📈 {result}")

        # Test 3: Buy 2 shares of IDEA
        print("\n3️⃣ Buying 2 shares of IDEA:")
        buy_input = BuyStockInput(
            stock="IDEA",
            qty=2,
            exchange="NSE",
            product="CNC",
            order_type="MARKET"
        )
        result = await buy_stock(buy_input)
        print(f"📈 {result}")

        # Test 4: Sell all GTLINFRA shares
        print("\n4️⃣ Selling all GTLINFRA shares:")
        sell_input = SellStockInput(
            stock="GTLINFRA",
            qty=2,
            exchange="NSE",
            product="CNC",
            order_type="MARKET"
        )
        result = await sell_stock(sell_input)
        print(f"📉 {result}")

        # Test 5: Sell all IDEA shares
        print("\n5️⃣ Selling all IDEA shares:")
        sell_input = SellStockInput(
            stock="IDEA",
            qty=2,
            exchange="NSE",
            product="CNC",
            order_type="MARKET"
        )
        result = await sell_stock(sell_input)
        print(f"📉 {result}")

        # Test 6: Show final portfolio
        print("\n6️⃣ Final Portfolio Check:")
        final_portfolio = await show_portfolio(EmptyInput())

        if 'content' in final_portfolio and len(final_portfolio['content']) > 0:
            portfolio_text = final_portfolio['content'][0]['text']
            print("📊 Final Portfolio:")
            print("=" * 50)

            lines = portfolio_text.split('\n')
            for line in lines:
                if line.strip():
                    if line.startswith('Current Portfolio:'):
                        print(f"💼 {line}")
                    elif 'stock:' in line:
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            stock = parts[0].replace('stock: ', '')
                            qty = parts[1].replace('qty: ', '')
                            price = parts[2].replace('currentPrice: ', '')

                            if float(qty) > 0:
                                print(f"📈 {stock:<20} | Qty: {qty:>8} | Price: ₹{price}")
                            else:
                                print(f"📊 {stock:<20} | Qty: {qty:>8} | Price: ₹{price} (No position)")
            print("=" * 50)
        else:
            print(f"📊 Final Portfolio: {final_portfolio}")

        print("\n🎉 Trading sequence completed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
