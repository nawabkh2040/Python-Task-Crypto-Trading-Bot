import os

api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')



from binance import Client

class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret)
