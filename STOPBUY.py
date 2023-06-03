from RSI_NUVA import inter
import pandas as pd
from io import StringIO
from APIConnect.APIConnect import APIConnect
from constants.asset_type import AssetTypeEnum
from constants.chart_exchange import ChartExchangeEnum
from constants.eod_Interval import EODIntervalEnum
from constants.intraday_interval import IntradayIntervalEnum
import os
from dateutil.relativedelta import relativedelta, TH
import datetime
from datetime import datetime
import time
import json
import numpy as np
from csv import writer
import shutil


class RSI_EMA():
    def __init__(self):
        pass

    def session_activate(self):
        df = pd.read_csv(r'C:\Users\Lenovo\Desktop\Kiteconnect/IRYS.csv')
        apikey = df['api_key'][0].strip()
        key_ = df['api_secret'][0].strip()
        request_token = open(r"C:\Users\Lenovo\Downloads\nuvarequest_token.txt", 'r').read()
        self.nuva = APIConnect(apikey, key_, request_token, True,
                               r'C:\Users\Lenovo\Desktop\Kiteconnect\python-settings.ini')

    def datadump(self):
        df_ = pd.read_csv(r'C:\Users\Lenovo\Desktop\instruments.csv')
        self.df = df_

    def exchange_symbol(self, ticker):
        c_random = self.df[(self.df["symbolname"] == ticker)]

        a = c_random['tradingsymbol'].to_list()
        ex = c_random['exchangetoken'].to_list()

        for k, i in enumerate(a):
            if i[-6:] == 'APRFUT':
                pri = ex[k]
                print(pri)
                return pri

    def getcmp(self, ticker):
        pa = ''

        for i in range(10):
            print(i)
            try:
                with inter('d2', self.nuva, ticker) as pp:
                    if len(pp) != 0:
                        pa = pp
                        break
            except:
                pass
        return pa

    def trade(self, exchangetoken):
        check_order_pe = 0
        for i in range(10):
            try:

                with inter('b0', self.nuva, [exchangetoken]) as trade_price:
                    # dict_data['trading_price']=trade_price[0]
                    if len(trade_price) != 0:
                        pe_signal_b = trade_price[0]['response']['data'].get('b0')
                        pe_signal_c = trade_price[0]['response']['data'].get('b1')
                        check_order_pe = (float(pe_signal_b[0].get('z0')) + float(pe_signal_c[0].get('z0'))) / 2
                        break
            except:
                pass
        print(check_order_pe, 'cop')
        return check_order_pe

    def Get_symbole(self, ticker, exchangetoken):
        next_thursday_expiry = datetime.today(
        ) + relativedelta(weekday=TH(1))
        pr = next_thursday_expiry.strftime("%d/%b/%y").upper()
        self.list_csv = {}
        atm_ = self.getcmp([exchangetoken])
        atmstric = round(float(atm_), -2)
        self.list_csv['atmstric'] = float(atm_)
        list_option = ['PE', 'CE']
        for OPTION in list_option:
            list_data = []
            for i in self.df.index:
                if self.df['expiry'][i] == str(pr) and self.df['symbolname'][i] == ticker and self.df['optiontype'][
                    i] == OPTION and self.df['strikeprice'][i] == atmstric:
                    list_data.append(self.df['tradingsymbol'][i])
                    list_data.append(self.df['exchangetoken'][i])
                    list_data.append(self.df['lotsize'][i])
                    gg = 'tradingsymbol{}'.format(OPTION)
                    self.list_csv[gg] = list_data[0]
                    self.list_csv['exchangetoken{}'.format(OPTION)] = list_data[1]
                    self.list_csv['lotsize'] = list_data[2]

                    hh = self.trade(list_data[1])
                    self.list_csv['trading_price{}'.format(OPTION)] = hh
            print(list_data, 'ld')
        print(self.list_csv, 'lc')

    def fetchOHLC(self, exchangetoken):
        response = self.nuva.getIntradayChart(ChartExchangeEnum.NFO, AssetTypeEnum.FUTIDX, exchangetoken,
                                              IntradayIntervalEnum.M5, TillDate=None, IncludeContinuousFutures=False)
        NFO = json.loads(response)
        NFO_Data = NFO['data']
        NFO_DF = pd.DataFrame(NFO_Data)
        return NFO_DF

    def EMA(self, DF, a):
        df = DF.copy()
        df["MA"] = df[4].ewm(span=a, min_periods=a).mean()
        df.dropna(inplace=True)
        return df

    def rsi(self, df, n):
        "function to calculate RSI"
        delta = df[4].diff().dropna()
        u = delta * 0
        d = u.copy()
        u[delta > 0] = delta[delta > 0]
        d[delta < 0] = -delta[delta < 0]
        u[u.index[n - 1]] = np.mean(u[:n])  # first value is average of gains
        u = u.drop(u.index[:(n - 1)])
        d[d.index[n - 1]] = np.mean(d[:n])  # first value is average of losses
        d = d.drop(d.index[:(n - 1)])
        rs = u.ewm(com=n, min_periods=n).mean() / d.ewm(com=n, min_periods=n).mean()
        return 100 - 100 / (1 + rs)

    def DataFrame_data_extrct(self, short_put, ticker, exchangetoken):
        c_random = self.df[(self.df["symbolname"] == ticker) & (
                self.df['tradingsymbol'].str[len(ticker) + 2:len(ticker) + 2 + 3] == 'APR')]
        print(c_random)
        a = c_random['tradingsymbol'].to_list()
        print(a, 'aaaaaa')
        b = c_random['exchangetoken'].to_list()
        c = c_random['lotsize'].to_list()
        xe = c_random['strikeprice'].to_list()
        self.atmstr = float(self.getcmp([exchangetoken])[0])
        print(self.atmstr, 'atm')

        if short_put == 'Red':
            gg = 0
            index = 0
            for en, j in enumerate(xe):
                if self.atmstr > j > 0:
                    if gg < j:
                        gg = j
                        index = en
                        print(index, 'hhhhh')
            return [a[index], b[index], c[index], self.atmstr]
        else:
            gg = 100000000
            index = 0
            for en, j in enumerate(xe):
                if self.atmstr < j > 0:
                    if gg > j:
                        gg = j
                        index = en
                        print(index, j, 'hhh')
            return [a[index], b[index], c[index], self.atmstr]

    def stoploss(self, ohlc, symbol):
        if symbol == 'C':
            print(ohlc["EMA_Slow"].iloc[-2], ohlc[4].iloc[-2])
            if ohlc["EMA_Slow"].iloc[-2] < ohlc[4].iloc[-2]:
                return 'stop'
        else:
            print(ohlc["EMA_Slow"].iloc[-2], ohlc[4].iloc[-2])
            if ohlc["EMA_Slow"].iloc[-2] > ohlc[4].iloc[-2]:
                return 'stop'

    def csv_a(self, ticker, List):

        with open(r'C:\Users\Lenovo\Desktop\RSI_EMA\rsi_sand\{}'.format(ticker), 'a') as f_object:
            writer_object = writer(f_object)

            writer_object.writerow(List)

            f_object.close()

    def rs_dir_refresh(self, ohlc):
        if ohlc["rs1"].iloc[-2] > 60 and ohlc["rs1"].iloc[-3] < 60 and ohlc[4].iloc[-1] > ohlc["EMA_Slow"].iloc[-1]:
            return "Green"
        if ohlc["rs1"].iloc[-2] < 40 and ohlc["rs1"].iloc[-3] > 40 and ohlc[4].iloc[-1] < ohlc["EMA_Slow"].iloc[-1]:
            return "Red"

    def main(self):
        entries = os.listdir(r'C:\Users\Lenovo\Desktop\RSI_EMA\rsi_sand')
        print(entries)
        for ticter_ in entries:
            ticker = ticter_.replace('.csv', '')
            df = pd.read_csv(r'C:\Users\Lenovo\Desktop\RSI_EMA\rsi_sand\{}'.format(ticter_))
            df_tolist = df.values.tolist()
            df_tolist_ = df_tolist[0]
            time.sleep(10)
            ticker_sb = self.exchange_symbol(ticker)
            ohlc = self.fetchOHLC(ticker_sb)
            ema = self.EMA(ohlc, 20)
            ohlc["EMA_Slow"] = ema['MA']
            ohlc_ = self.rsi(ohlc, 14)
            ohlc["rs1"] = ohlc_
            current_price = ohlc[4].iloc[-1]
            signal = self.rs_dir_refresh(ohlc)
            symbol_ = df_tolist_[2][-2:-1]
            print(symbol_, "symbol_")
            tradingSymbol__ = df_tolist_[-1]
            print(tradingSymbol__, "tradingSymbol__")
            print(type(tradingSymbol__))
            atm_strik = (self.getcmp([tradingSymbol__]))
            print(atm_strik, 'atm_strik')
            time.sleep(2)
            current_market = self.trade(tradingSymbol__)
            if current_market != 0:
                print(current_market, "current_market")
                pnl_ = (-current_market + df_tolist_[4]) * df_tolist_[3]
                print(pnl_, "pnl_")
                List = [signal, current_price, df_tolist_[2], df_tolist_[3], df_tolist_[5], current_market, pnl_,
                        datetime.now(),
                        ohlc["rs1"].iloc[-1], ohlc["rs1"].iloc[-2], ohlc["rs1"].iloc[-3], ohlc["EMA_Slow"].iloc[-1],
                        df_tolist_[-1]]
                self.csv_a(ticter_, List)
                stop_ = self.stoploss(ohlc, symbol_)
                if stop_ != None:
                    ticter_12 = str(ticker) + str(datetime.now().strftime('%H%m%S')) + '.csv'
                    print(ticter_12)
                    for i in range(10):
                        try:
                            shutil.move(r'C:\Users\Lenovo\Desktop\RSI_EMA\rsi_sand\{}'.format(ticter_),
                                        r'C:\Users\Lenovo\Desktop\RSI_EMA\history_data\{}'.format(ticter_12))
                            break

                        except Exception as p:
                            print(p)

    def __enter__(self):
        self.datadump()
        self.session_activate()
        for i in range(1000000000):
            self.main()
            time.sleep(60)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


with RSI_EMA() as p:
    pass
