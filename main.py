import os
import time
import hmac
import hashlib
import logging
import requests
import argparse
import sys

# Binance Futures Testnet base URL (USDT-M)
TESTNET_FUTURES_BASE = os.getenv('BINANCE_FUTURES_TESTNET', 'https://testnet.binancefuture.com')


class BasicBot:
    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_FUTURES_BASE):
        if not api_key or not api_secret:
            raise ValueError('API key and secret are required')
        self.api_key = api_key
        self.api_secret = api_secret.encode('utf-8')
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'X-MBX-APIKEY': self.api_key, 'Content-Type': 'application/x-www-form-urlencoded'})

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, data: str) -> str:
        return hmac.new(self.api_secret, data.encode('utf-8'), hashlib.sha256).hexdigest()

    def _signed_request(self, method: str, path: str, params: dict):
        params = params or {}
        params['timestamp'] = self._timestamp()
        query = '&'.join([f"{k}={params[k]}" for k in sorted(params)])
        signature = self._sign(query)
        query = f"{query}&signature={signature}"
        url = f"{self.base_url}{path}?{query}"
        logging.debug('Request URL: %s', url)
        try:
            resp = self.session.request(method, url, timeout=10)
            logging.info('Request: %s %s', method, url)
            logging.info('Response code: %s', resp.status_code)
            logging.debug('Response text: %s', resp.text)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logging.exception('HTTP request failed')
            raise

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, stopPrice: float = None, timeInForce: str = 'GTC', reduceOnly: bool = False):
        """
        Place an order on Binance Futures Testnet.
        Supported order types: MARKET, LIMIT, STOP_LIMIT (simplified)
        """
        symbol = symbol.upper()
        side = side.upper()
        order_type = order_type.upper()

        if side not in ('BUY', 'SELL'):
            raise ValueError('side must be BUY or SELL')
        if order_type not in ('MARKET', 'LIMIT', 'STOP_LIMIT'):
            raise ValueError('order_type must be MARKET, LIMIT, or STOP_LIMIT')
        if quantity <= 0:
            raise ValueError('quantity must be > 0')

        path = '/fapi/v1/order'
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET' if order_type == 'MARKET' else ('LIMIT' if order_type == 'LIMIT' else 'STOP'),
            'quantity': float(quantity),
            'reduceOnly': 'true' if reduceOnly else 'false',
        }

        if order_type == 'LIMIT':
            if price is None:
                raise ValueError('price is required for LIMIT orders')
            params.update({'price': float(price), 'timeInForce': timeInForce})

        if order_type == 'STOP_LIMIT':
            if stopPrice is None or price is None:
                raise ValueError('stopPrice and price are required for STOP_LIMIT orders')
            params.update({'stopPrice': float(stopPrice), 'price': float(price)})

        result = self._signed_request('POST', path, params)
        return result


def setup_logging(log_file: str = 'bot.log'):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[
                            logging.FileHandler(log_file),
                            logging.StreamHandler(sys.stdout)
                        ])


def parse_args():
    p = argparse.ArgumentParser(description='Simplified Binance Futures Testnet trading bot')
    p.add_argument('--api-key', help='Binance API key (or set API_KEY env var)')
    p.add_argument('--api-secret', help='Binance API secret (or set API_SECRET env var)')
    p.add_argument('--symbol', required=True, help='Trading symbol, e.g., BTCUSDT')
    p.add_argument('--side', required=True, choices=['BUY', 'SELL'], help='BUY or SELL')
    p.add_argument('--type', required=True, choices=['MARKET', 'LIMIT', 'STOP_LIMIT'], help='Order type')
    p.add_argument('--quantity', required=True, type=float, help='Order quantity')
    p.add_argument('--price', type=float, help='Price for LIMIT / STOP_LIMIT')
    p.add_argument('--stop-price', type=float, dest='stop_price', help='Stop price for STOP_LIMIT')
    p.add_argument('--base-url', default=TESTNET_FUTURES_BASE, help='Base URL for Binance Futures Testnet')
    return p.parse_args()


def main():
    setup_logging()
    args = parse_args()
    api_key = args.api_key or os.getenv('API_KEY')
    api_secret = args.api_secret or os.getenv('API_SECRET')
    bot = BasicBot(api_key, api_secret, base_url=args.base_url)

    try:
        resp = bot.place_order(symbol=args.symbol, side=args.side, order_type=args.type, quantity=args.quantity, price=args.price, stopPrice=args.stop_price)
        print('Order placed:')
        print(resp)
        logging.info('Order result: %s', resp)
    except Exception as e:
        print('Error placing order:', str(e))
        logging.exception('Failed to place order')


if __name__ == '__main__':
    main()
