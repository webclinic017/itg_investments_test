import time
from config import load_config
from binance.client import Client
import numpy as np
import talib
import csv

client = Client(api_key=load_config().binance_api.api_testnet, api_secret=load_config().binance_api.api_testnet_secret,
                testnet=True)


class Strategy:

    def __init__(self, symbol='BTCUSDT', client=client, order_size=0.02, long_tp_perc=0.01, short_tp_perc=0.004,
                 asset='USDT',
                 leverage=10, interval='1h', limit='200'):
        self.symbol = symbol
        self.leverage = leverage
        self.order_size = order_size
        self.long_tp_perc = long_tp_perc
        self.short_tp_perc = short_tp_perc
        self.asset = asset
        self.client = client
        self.interval = interval
        self.limit = limit

    def get_entry_price(self):
        return float(self.client.futures_position_information(symbol='BTCUSDT')[0]['entryPrice'])

    def get_ticker_price(self):
        return float(self.client.futures_ticker(symbol=self.symbol)['lastPrice'])

    def get_data(self):
        res = self.client.futures_klines(symbol=self.symbol, interval=self.interval, limit=self.limit)
        return_data = []
        for each in res:
            return_data.append(float(each[4]))
        return np.array(return_data)

    def get_balance(self):
        balances = self.client.futures_account_balance()
        asset_balance = 0
        for balance in balances:
            if balance['asset'] == self.asset:
                asset_balance = balance['balance']
                break
        return float(asset_balance)

    def initialise_futures(self):
        return self.client.futures_change_leverage(symbol=self.symbol, leverage=self.leverage)

    def adjust_order_size_usdt(self):
        return self.get_balance() * self.order_size

    def adjust_order_size_btc(self):
        return round(self.adjust_order_size_usdt() / self.get_ticker_price(), 3)

    def adjust_long_tp_perc(self):
        return round(self.get_entry_price() * (1 + self.long_tp_perc))

    def adjust_short_tp_perc(self):
        return self.get_entry_price() * (1 - self.short_tp_perc)

    def get_account_trades(self):
        trades = self.client.futures_account_trades(symbol=self.symbol)
        keys = trades[0].keys()
        with open('trades.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            writer.writeheader()
            writer.writerows(trades)
        return f'trades.csv'

    def place_order_long(self, order_type):
        stop_price = self.adjust_long_tp_perc()
        quantity = self.adjust_order_size_btc()
        if order_type == "BUY":
            self.client.futures_create_order(symbol=self.symbol, side="BUY", quantity=quantity, type="MARKET")
        else:
            self.client.futures_create_order(symbol=self.symbol, side="SELL", quantity=quantity,
                                             type="TAKE_PROFIT_MARKET", stopPrice=stop_price)
        print("order placed successfully!")
        print(self.client.futures_position_information(symbol=self.symbol))
        return

    def place_order_short(self, order_type):
        stop_price = self.adjust_short_tp_perc()
        quantity = self.adjust_order_size_btc()
        if order_type == "BUY":
            self.client.futures_create_order(symbol=self.symbol, side="BUY", quantity=quantity,
                                             type="TAKE_PROFIT_MARKET", stopPrice=stop_price)
        else:
            self.client.futures_create_order(symbol=self.symbol, side="SELL", quantity=quantity,
                                             type="MARKET")
        print("order placed successfully!")
        print(self.client.futures_position_information(symbol='BTCUSDT'))
        return


def main():
    strategy = Strategy()
    buy_long = False
    sell_long = True
    buy_short = False
    sell_short = True

    last_sma_7 = 0
    last_sma_25 = 0
    print("Started")
    while True:
        closing_data = strategy.get_data()
        sma_7 = talib.SMA(closing_data, 7)[-1]
        sma_25 = talib.SMA(closing_data, 25)[-1]
        # long
        if sma_7 > sma_25 and last_sma_7:
            if last_sma_7 < last_sma_25 and not buy_long:
                print(f'entered long position')
                strategy.place_order_long('BUY')
                buy_long = True
                sell_long = False

        if sma_25 > sma_7 and last_sma_25:
            if last_sma_25 < last_sma_7 and not sell_long:
                print(f'closed long position')
                strategy.place_order_long('SELL')
                sell_long = True
                buy_long = False

        # short
        if sma_25 > sma_7 and last_sma_25:
            if last_sma_25 < last_sma_7 and not buy_short:
                print(f'entered short position')
                strategy.place_order_short('SELL')
                sell_short = True
                buy_short = False

        if sma_7 > sma_25 and last_sma_7:
            if last_sma_7 < last_sma_25 and not sell_short:
                print(f'closed short position')
                strategy.place_order_short('BUY')
                buy_short = True
                sell_short = False

        last_sma_7 = sma_7
        last_sma_25 = sma_25
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Stopped')
