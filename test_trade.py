import asyncio
from trade import place_order, get_positions

async def run():
    print("🛒 Testing BUY...")
    buy_response = await place_order("IDEA", 1, transaction_type="BUY")

    if buy_response.get("status") == "success":
        print(f"✅ {buy_response.get('message')}")
        print(f"📋 Order ID: {buy_response.get('order_id')}")
    else:
        print(f"❌ Buy failed: {buy_response.get('message')}")
        print(f"🔍 Error type: {buy_response.get('error_type')}")
        if buy_response.get('error_type') == 'trading_error':
            print("💡 This is a trading-related error (insufficient funds, market closed, etc.)")
        return

    print("\n📈 Portfolio:")
    positions = await get_positions()
    print(positions)

    print("\n💰 Testing SELL...")
    sell_response = await place_order("IDEA", 1, transaction_type="SELL")

    if sell_response.get("status") == "success":
        print(f"✅ {sell_response.get('message')}")
        print(f"📋 Order ID: {sell_response.get('order_id')}")
    else:
        print(f"❌ Sell failed: {sell_response.get('message')}")
        print(f"🔍 Error type: {sell_response.get('error_type')}")
        if "don't own this stock" in sell_response.get('message', ''):
            print("💡 This is expected - you need to own the stock before selling it!")

    print("\n📊 Final Portfolio:")
    final_positions = await get_positions()
    print(final_positions)

asyncio.run(run())
