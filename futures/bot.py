import pandas as pd
from time import sleep
from binance.client import Client
import f_config
import ta 
from termcolor import colored
import f_config



# client = Client(f_config.apiKey, f_config.apiSecurity)
# balance = client.get_asset_balance(asset = 'USDT')
# print(balance)

# order = client.futures_create_order(symbol="ADAUSDT", side="BUY", type="MARKET", quantity=20)
# print(order)

# info = client.futures_historical_klines('ADAUSDT', '15m', '10m UTC')
# # print(info)
#
#
# df = pd.DataFrame(client.get_historical_klines('ADAUSDT', '15m', '3600m UTC'))
# df = df.iloc[:,:6]
# df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
# df = df.set_index('Time')
# df.index = pd.to_datetime(df.index, unit='ms')
# df = df.astype(float)
# print(df)


client = Client(f_config.apiKey, f_config.apiSecurity)
print('logged in')

# client.futures_change_leverage(leverage=20)

class Bot:
    
    def __init__(self, symbol, time_interval, strategy, sleep_time):
        self.symbol = symbol 
        self.time_interval = time_interval
        self.strategy = strategy
        self.sleep_time = sleep_time
        self.buying_asset = symbol[0:3]
        self.stable_asset = symbol[3:len(symbol)+1]

    def acc_data(self, asset):
            balance = dict()
            balance = client.futures_account_balance(asset = asset)
            balance_ = balance[1]['balance']
            return balance_



    def get_min_data(self): 
        utc_time = str(int(self.time_interval) * 60) + 'm UTC'
        interval = str(self.time_interval) + 'm'
        time_err = True
        while time_err == True:
            try:
                df = pd.DataFrame(client.futures_historical_klines(self.symbol, interval, utc_time))
                time_err = False
            except:
                print('something wrong with Timeout')
                sleep(self.sleep_time) 

        df = df.iloc[:,:6]
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = df.set_index('Time')
        df.index = pd.to_datetime(df.index, unit='ms')
        df = df.astype(float)
        return df

    def place_order(self, side):
        if side == 'BUY':
            unrounded_qty = self.acc_data(self.stable_asset)
            unrounded_qty = float(unrounded_qty) - 0.01 * float(unrounded_qty)
            qty = int(round(unrounded_qty, 0))

        else:
            unrounded_qty = self.acc_data(self.buying_asset)
            unrounded_qty = float(unrounded_qty)  - 0.01 * float(unrounded_qty)
            qty = int(round(unrounded_qty, 0))

        qty_err = True
        while qty_err == True:
            try:
                order = client.futures_create_order(
                    symbol = self.symbol,
                    side = side,
                    type = 'MARKET',
                    quantity = qty,
                )
                qty_err = False
            except:
                print('something wrong with qty')
                sleep(self.sleep_time)
        return order



    def trading_strat(self, open_pos = False):
        while True:
            df = self.get_min_data()
            if not open_pos:
                if self.check_macd_open(df):
                    order = self.place_order('BUY')
                    open_pos = True
                    buyprice = float(order['fills'][0]['price'])
                    print('bought at', buyprice)
                    sleep(self.sleep_time)
                    break
                sleep(self.sleep_time)
        if open_pos:
            while True:
                df = self.get_min_data()
                if self.check_macd_close(df):
                    order = self.place_order('SELL')    #qty-(0.01*qty)
                    sellprice = float(order['fills'][0]['price'])
                    print('sold at', sellprice)
                    profit = sellprice - buyprice
                    print(colored(profit, 'yellow'))
                    open_pos = False
                    break
                sleep(self.sleep_time)

    #def curr_price(self):
        #avg_price = client.get_avg_price(symbol=self.symbol)
        #return avg_price['price']

    #def qty_calc(self, asset):
        #balance = self.acc_data(asset)
        #price = self.curr_price()
        #amount = (float(balance)-3) / float(price)
        #amount = round(amount, 0)
        #return amount
        
    def check_macd_open(self, df):
        buy_sig = False
        # print(ta.trend.macd_diff(df.Close))
        # print(ta.trend.macd_diff(df.Close).iloc[-1])
        if ta.trend.macd_diff(df.Close).iloc[-1] > 0 \
        and ta.trend.macd_diff(df.Close).iloc[-2] < 0:
            buy_sig = True
            return buy_sig

    def check_macd_close(self, df):
        sell_sig = False
        if ta.trend.macd_diff(df.Close).iloc[-1] < ta.trend.macd_diff(df.Close).iloc[-3]:
            sell_sig = True
            return sell_sig

    def start(self):
        client.futures_change_leverage(symbol=self.symbol, leverage=20)

        while True:
            print(colored(self.acc_data(self.stable_asset), 'green'))
            self.trading_strat()


macd_bot = Bot('ADAUSDT',15, 'macd', 60)

macd_bot.start()
