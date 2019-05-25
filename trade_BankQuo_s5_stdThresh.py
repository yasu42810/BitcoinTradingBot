import numpy as np
import pandas as pd
import ccxt
import python_bitbankcc
import json
import urllib
import requests
import time
import datetime
import csv

# ファイルオープン
today = datetime.datetime.today()
f = open("{}{}{}_{}{}{}".format(str(today.year), str(today.month).zfill(2), str(today.day).zfill(2),
                       str(today.hour).zfill(2), str(today.minute).zfill(2), str(today.second).zfill(2)), "a")
writer = csv.writer(f)
data =["date", "ask/bank", "bid/bank", "ask/quo", "bid/quo"]
writer.writerow(data)

# bitbankのAPIキーとAPIシークレット
API_KEY = ""
API_SECRET = ""

quoinex = ccxt.quoinex()
bitbank_prv = python_bitbankcc.private(API_KEY, API_SECRET)
bitbank_pub = python_bitbankcc.public()


# bitbankがquoinexの上にあるか下にあるか
flagTradeAbove = False
flagTradeBelow = False

#　ティッカーと取引所の状況を取得
# 引数:なし
# 戻り値 : bank_ticker_dict(ask, bid), quo_ticker_dict(ask, bid)
def get_ticker():
    while True:
        try:
            ticker_quo = quoinex.fetch_ticker("BTC/JPY")
            ticker_bank = bitbank_pub.get_ticker("btc_jpy")
            break
        except:
            print("Error getting rate.")
    ticker_quo = {"ask":int(ticker_quo["ask"]), "bid":int(ticker_quo["bid"])}
    ticker_bank = {"ask":int(ticker_bank["sell"]), "bid":int(ticker_bank["buy"])}
    return ticker_bank, ticker_quo


# -------------------------取引スタート------------------------

WINDOW = 100
THRESHOLD = 200 # 乖離の閾値
param = 2 # 標準偏差 : n sigma
profit_bank = 0
profit_quo = 0
hist = []
now = datetime.datetime.now().timestamp()
pre = now
count = 0
size = 0.1 # 取引量
for i in range(WINDOW-1):
    ticker_bank, ticker_quo = get_ticker()
    hist.append(ticker_bank["ask"] - ticker_quo["ask"])
    print(hist)
    while now - pre < 5:
        now = datetime.datetime.now().timestamp()
        time.sleep(0.001)
    pre = now
while True:
    # 値の取得
    ticker_bank, ticker_quo = get_ticker()
    gapNow = ticker_bank["ask"] - ticker_quo["ask"]
    hist.append(gapNow)

    base = np.array(hist).mean() # 平均値
    sigma = np.array(hist).std() # 標準偏差
    upper_sigma = base + sigma * param # 正の乖離
    lower_sigma = base - sigma * param # 負の乖離

    if not flagTradeAbove and not flagTradeBelow: # 注文中でない
        """if upper_sigma < gapNow and sigma > THRESHOLD:
            # 注文　bank売り quo買い
            while True:
                try:
                    bitbank_prv.order("btc_jpy", str(int(ticker_bank["bid"])-10000), str(size), "sell", "market")
                    break
                except Exception as e:
                    print("Error:"+str(e))
                    if "60001" in str(e):
                        print("Not enough amount!")
                        time.sleep(1)
                    elif "700" in str(e):
                        print("System Error!")
                        time.sleep(1)
                    else:
                        print("Another Error. Exit!")
                        exit()

            bank_rate = ticker_bank["bid"]
            quo_rate = ticker_quo["ask"]
            flagTradeAbove = True
            print("Above 2σ! Start.")"""
        if lower_sigma > gapNow and sigma > THRESHOLD:
            # 注文　bank買い quo売り
            while True:
                try:
                    bitbank_prv.order("btc_jpy", str(int(ticker_bank["ask"])+10000), str(size), "buy", "market")
                    break
                except Exception as e:
                    print("Error:"+str(e))
                    if "60001" in str(e):
                        print("Not enough amount!")
                        time.sleep(1)
                    elif "700" in str(e):
                        print("System Error!")
                        time.sleep(1)
                    else:
                        print("Another Error. Exit!")
                        exit()
            bank_rate = ticker_bank["ask"]
            quo_rate = ticker_quo["bid"]
            flagTradeBelow = True
            print("Below 2σ! Start.")
    else:
        """if flagTradeAbove and lower_sigma > gapNow:
            # 決済　bank買い quo売り
            while True:
                try:
                    bitbank_prv.order("btc_jpy", str(int(ticker_bank["ask"])+10000), str(size), "buy", "market")
                    break
                except Exception as e:
                    print("Error:"+str(e))
                    if "60001" in str(e):
                        print("Not enough amount!")
                        time.sleep(1)
                    elif "700" in str(e):
                        print("System Error!")
                        time.sleep(1)
                    else:
                        print("Another Error. Exit!")
                        exit()
            flagTradeAbove = False
            flagTradeBelow = True
            profit_bank += (bank_rate - ticker_bank["ask"])*size
            profit_quo += (ticker_quo["bid"] - quo_rate)*size
            bank_rate = ticker_bank["ask"]
            quo_rate = ticker_quo["bid"]
            print("Above. Settlement.")"""
        if flagTradeBelow and upper_sigma < gapNow:
            # 決済　bank売り quo買い
            while True:
                try:
                    bitbank_prv.order("btc_jpy", str(int(ticker_bank["bid"])-10000), str(size), "sell", "market")
                    break
                except Exception as e:
                    print("Error:"+str(e))
                    if "60001" in str(e):
                        print("Not enough amount!")
                        time.sleep(1)
                    elif "700" in str(e):
                        print("System Error!")
                        time.sleep(1)
                    else:
                        print("Another Error. Exit!")
                        exit()
            #flagTradeAbove = True
            flagTradeBelow = False
            profit_bank += (ticker_bank["bid"] - bank_rate)*size
            profit_quo += (quo_rate - ticker_quo["ask"])*size
            #bank_rate = ticker_bank["bid"]
            #quo_rate = ticker_quo["ask"]
            print("Below. Settlement.")

    hist.pop(0)
    # 書き込み　
    data = []
    today = datetime.datetime.today()
    data.append("{}{}{}/{}{}{}".format(str(today.year), str(today.month).zfill(2), str(today.day).zfill(2),
                       str(today.hour).zfill(2), str(today.minute).zfill(2), str(today.second).zfill(2)))
    # bitbank
    data.append(ticker_bank["ask"])
    data.append(ticker_bank["bid"])
    # bidquoerFX
    data.append(ticker_quo["ask"])
    data.append(ticker_quo["bid"])
    writer.writerow(data)

    print(data)
    print("size:{}".format(size))
    print("bank_profit:{}".format(profit_bank))
    print("quoinex_profit:{}".format(profit_quo))
    print("flagTradeAbove : {}" .format(flagTradeAbove))
    print("flagTradeBelow : {}" .format(flagTradeBelow))
    print("Gap : {}   STD : {}\n".format(ticker_bank["ask"] - ticker_quo["ask"], sigma))

    while now - pre < 5:
        now = datetime.datetime.now().timestamp()
        time.sleep(0.001)
    pre = now
