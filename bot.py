#!/usr/bin/env python3
import os
import math
import decimal
import logging
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

load_dotenv()

# ---------------- LOGGING ---------------- #
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------- Helpers ---------------- #
def to_decimal(x):
    return Decimal(str(x))

def floor_to_step(qty: Decimal, step: Decimal) -> Decimal:
    # floor to nearest multiple of step
    if step == 0:
        return qty
    mul = (qty / step).to_integral_value(rounding=ROUND_DOWN)
    return (mul * step).normalize()

def ceil_to_step(qty: Decimal, step: Decimal) -> Decimal:
    if step == 0:
        return qty
    mul = (qty / step).to_integral_value(rounding=ROUND_UP)
    return (mul * step).normalize()

# ---------------- BOT CLASS ---------------- #
class BasicBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        if testnet:
            # ensure testnet base url usage in python-binance
            try:
                self.client.FUTURES_URL = "https://testnet.binancefuture.com"
            except Exception:
                pass
        logger.info("Binance Futures Testnet Bot Initialized")

    def get_usdt_available(self) -> Decimal:
        balances = self.client.futures_account_balance()
        for b in balances:
            if b["asset"] == "USDT":
                return to_decimal(b.get("availableBalance", b.get("balance", "0")))
        return Decimal("0")

    def get_symbol_filters(self, symbol: str):
        info = self.client.futures_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol:
                # default values
                stepSize = Decimal("0")
                minQty = Decimal("0")
                minNotional = Decimal("0")
                for f in s.get("filters", []):
                    if f["filterType"] == "LOT_SIZE":
                        stepSize = Decimal(f.get("stepSize", "0"))
                        minQty = Decimal(f.get("minQty", "0"))
                    if f["filterType"] in ("MIN_NOTIONAL", "MIN_NOTIONAL"):
                        # some payloads use 'minNotional' or 'notional'
                        minNotional = Decimal(f.get("notional", f.get("minNotional", "0")))
                return {"stepSize": stepSize, "minQty": minQty, "minNotional": minNotional}
        raise ValueError(f"Symbol {symbol} not found in exchange info")

    def get_mark_price(self, symbol: str) -> Decimal:
        res = self.client.futures_mark_price(symbol=symbol)
        # python-binance may return list or dict
        if isinstance(res, list):
            price = res[0]["markPrice"]
        elif isinstance(res, dict) and "markPrice" in res:
            price = res["markPrice"]
        else:
            # fallback to ticker price
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = ticker.get("price")
        return to_decimal(price)

    def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED"):
        try:
            self.client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
            logger.info(f"Set margin type {margin_type} for {symbol}")
        except BinanceAPIException as e:
            # sometimes Binance says "no need to change", ignore that
            logger.debug(f"set_margin_type response: {e}")

    def set_leverage(self, symbol: str, leverage: int):
        # leverage must be int and within allowed range per symbol (API enforces)
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info(f"Set leverage {leverage} for {symbol}")
        except BinanceAPIException as e:
            logger.error(f"Failed to set leverage: {e}")
            raise

    def validate_and_prepare_quantity(self, symbol: str, requested_qty: Decimal, leverage: int):
        filters = self.get_symbol_filters(symbol)
        step = filters["stepSize"]
        minQty = filters["minQty"]
        minNotional = filters["minNotional"]

        price = self.get_mark_price(symbol)
        logger.info(f"{symbol} mark price: {price}")

        # round requested qty down to step multiple (so we won't send invalid precision)
        qty_adj = floor_to_step(requested_qty, step) if step != 0 else requested_qty

        # ensure qty >= minQty
        if minQty > 0 and qty_adj < minQty:
            qty_adj = minQty

        notional = qty_adj * price

        # if notional < minNotional, try to raise qty to meet minNotional (ceil to step).
        if minNotional > 0 and notional < minNotional:
            target_qty = ( (minNotional / price).quantize(step, rounding=ROUND_UP) 
                           if step != 0 else (minNotional / price) )
            # use ceil_to_step to ensure step alignment
            qty_adj = ceil_to_step(to_decimal(target_qty), step) if step != 0 else to_decimal(target_qty)
            notional = qty_adj * price

        # final step: ensure notional >= minNotional
        if minNotional > 0 and notional < minNotional:
            raise ValueError(f"After adjustment quantity {qty_adj} still has notional {notional} < minNotional {minNotional}")

        return qty_adj, price, notional, filters

    def estimate_required_margin(self, notional: Decimal, leverage: int) -> Decimal:
        # initial margin (approx) = notional / leverage
        # add small buffer (10%)
        margin = notional / Decimal(leverage)
        return (margin * Decimal("1.1")).quantize(Decimal("0.00000001"))

    # order methods
    def place_market_order(self, symbol: str, side: str, quantity: Decimal):
        try:
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type="MARKET",
                quantity=float(quantity)
            )
            logger.info(f"Market Order Success: {order}")
            return order
        except (BinanceAPIException, BinanceOrderException) as e:
            logger.error(e)
            raise

# ---------------- CLI ---------------- #
def cli():
    # load from environment
    API_KEY = os.getenv("BINANCE_API_KEY"," ")
    API_SECRET = os.getenv("BINANCE_API_SECRET"," ")
    if not API_KEY or not API_SECRET:
        print("❌ API keys missing in environment. Put them into .env (BINANCE_API_KEY and BINANCE_API_SECRET).")
        return

    bot = BasicBot(API_KEY, API_SECRET, testnet=True)

    print("\n=== Binance Futures Testnet Bot ===")
    symbol = input("Symbol (e.g. BTCUSDT / ETHUSDT): ").strip().upper()
    side = input("Side (BUY / SELL): ").strip().upper()
    order_type = input("Order Type (MARKET only for this flow): ").strip().upper()
    qty_in = input("Quantity (e.g. 0.003): ").strip()
    leverage_in = input("Desired Leverage (e.g. 20): ").strip()

    try:
        requested_qty = to_decimal(qty_in)
        leverage = int(leverage_in)
    except Exception as e:
        print("Invalid numeric inputs:", e)
        return

    # 1) set margin type and leverage for the target symbol
    bot.set_margin_type(symbol, "ISOLATED")
    bot.set_leverage(symbol, leverage)

    # 2) compute adjustments & validate
    try:
        qty_adj, mark_price, notional, filters = bot.validate_and_prepare_quantity(symbol, requested_qty, leverage)
    except Exception as e:
        print("Quantity/Notional validation failed:", e)
        # helpful suggestion: try ETHUSDT or larger quantity
        print("Suggestion: Try a larger quantity, higher leverage, or a cheaper symbol like ETHUSDT.")
        return

    available_usdt = bot.get_usdt_available()
    required_margin = bot.estimate_required_margin(notional, leverage)

    print(f"\nSymbol: {symbol}")
    print(f"Mark price: {mark_price}")
    print(f"Requested qty: {requested_qty} -> Adjusted qty: {qty_adj}")
    print(f"Notional: {notional:.2f} USDT")
    print(f"Available USDT: {available_usdt}")
    print(f"Estimated required margin (with buffer): {required_margin:.6f} USDT")

    if available_usdt < required_margin:
        print("\n❌ Insufficient available USDT for this order.")
        print("Options:")
        print(" - Increase leverage (if allowed), OR")
        print(" - Use a cheaper symbol (e.g., ETHUSDT), OR")
        print(" - Fund your testnet wallet from the testnet faucet.")
        return

    # finally place the order
    try:
        if order_type == "MARKET":
            res = bot.place_market_order(symbol, side, qty_adj)
            print("\n✅ Market order placed.")
            print("Order ID:", res.get("orderId"))
            print("Status:", res.get("status"))
            print("Executed Qty:", res.get("executedQty"))
        else:
            print("Only MARKET type implemented in this flow. Add similar validation for LIMIT/STOP if needed.")
    except Exception as e:
        print("Order placement failed:", e)

if __name__ == "__main__":
    cli()
