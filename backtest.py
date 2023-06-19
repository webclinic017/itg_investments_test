import backtrader as bt
from binance.client import Client
from config import load_config
import pandas as pd


def get_data(symbol='BTCUSDT', interval='1h', start='2022-01-01', end='2022-12-31'):
    client = Client(api_key=load_config().binance_api.api_key, api_secret=load_config().binance_api.api_secret)
    klines = client.get_historical_klines(symbol=symbol, interval=interval, start_str=start, end_str=end)

    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                       'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                       'taker_buy_quote_asset_volume', 'ignore'])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df


class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(

        pfast=7,  # period for the fast moving average
        pslow=25  # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position


cerebro = bt.Cerebro()

df = get_data()
feed = bt.feeds.PandasData(dataname=df)

cerebro.adddata(feed)

cerebro.addstrategy(SmaCross)  # Add the trading strategy
cerebro.addsizer(bt.sizers.PercentSizer, percents=2)
cerebro.broker.setcommission(commission=0.01)
cerebro.run()  # run it all
cerebro.plot()  # and plot it with a single command
