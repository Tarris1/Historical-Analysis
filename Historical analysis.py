# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 16:45:56 2019

@author: Sandsnes
"""
import pandas as pd
from datetime import datetime
from iexfinance.stocks import (Stock, get_historical_data, get_historical_intraday, 
                               get_ipo_calendar, get_collections)
#import matplotlib.pyplot as plt
import math
import quandl
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

def import_data(stock, start, end):
    '''Imports daily stock data using iexfinance.stocks API, 
    calculates daily returns and returns it in pandas format.
    @params. stock = ticker symbol
    @params. start = datetime object, starting date
    @params. end = datetime object, end date. ***Max 5 years of data***'''
    
    df = get_historical_data(stock, start, end, output_format = "pandas")
    dret = []
    df_close = df['close']
    for i in range(len(df_close)):
        if i < len(df_close)-1:
            dret.append(math.log((df_close[i+1]/df_close[i])))
    dret.append(0)
    df["Returns"] = dret
    return df

def import_multiple(data_to_return, names, start, end):
    '''Returns daily returns of all tickers in names 
    in stock_and_returns[0]. All stock data for each stock in[1]
    
    @Params. data_to_return: what type of data you want, options: close, open
    , Returns, ++.
            names: list of ticker symbols.
    
    '''
    stock_and_returns = []
    stock_list = {}
    for i in range(len(names)):
        df = import_data(names[i], start, end)
        stock_list[names[i]] = df
        if i == 0:
            stocks = pd.DataFrame({names[i]:df[data_to_return]})
        else:
            stocks[names[i]] = df[data_to_return]
    stock_and_returns.append(stocks)
    stock_and_returns.append(stock_list)
    return stock_and_returns
 

def import_IPO():
    upcoming_IPOS = get_ipo_calendar()["viewData"]
    return upcoming_IPOS

def import_collections(sector):
    collection = get_collections(sector, output_format = 'pandas') #
    markCap = collection.loc["marketCap"]
    markCap = markCap.sort_values()
    top_ten = []
    indexing = len(markCap)-1
    top_notNA = 0
    while top_notNA < 10:
        test = math.isnan(markCap[indexing]) #Makes sure the data is a number
        if test == False:
            market_cap = markCap.iloc[indexing] ##Market Cap
            ticker = markCap.index[indexing] #Ticker
            top = {"Ticker": ticker, "Market Cap": market_cap}
            top_ten.append(top)
            top_notNA += 1
        indexing -= 1
    #companies = list(collection)
    return pd.DataFrame(top_ten)

def ReturnData(stock_data, start, end):
    '''Returns a dataframe with annualized daily means, st.dev, correlation, beta, alpha and sharpe ratio
    
    @Params. stock_data = dataframe from import_collections, start, end
    
    Error Message is returned if data entered is not a collection of returns
    '''
    if stock_data.iloc[-0,0]<=1:
        stock_data_corr = stock_data.corr()
        df = {"Mean": stock_data.mean()*100*252, "St. Dev.": stock_data.std()*100*252, 
              "SPY Corr": stock_data_corr["SPY"]}
        stocks_df = pd.DataFrame(df)
        SPY_std = stocks_df["St. Dev."]["SPY"]
        beta = stocks_df["SPY Corr"]*(SPY_std/stocks_df["St. Dev."])
        tbill = quandl.get("FRED/TB3MS", start_date=start, end_date=end) #Import 3month Tbill
        rrf = tbill.iloc[-1,0]
        ybar = stocks_df["Mean"]-rrf
        xbar = stocks_df["Mean"]["SPY"]-rrf
        alpha = (ybar)-beta*(xbar)
        sharpe = (ybar-rrf)/stocks_df["St. Dev."]
        stocks_df["Beta"] = beta
        stocks_df["Alpha"] = alpha
        stocks_df["Sharpe"] = sharpe
        return stocks_df
    else:
        Error = "Entered data is not a collection of returns\n"
        print(Error)
        return 0

def get_price(stock_data, names):
    price = []
    for i in range(len(stock_data[1])):
        price.append(stock_data[1][names[i]]["close"].iloc[-1])
    return price

def create_plot(data, ticker, loc):
    '''Plots 3 figures: daily returns, daily prices and daily trading volumes
    
    @Params. Data = Dataframe of iexfinance.stocks object.
            Ticker = Stock to compare with S&P500
            loc = name of plot
            
    '''
            
    comp = "SPY"
    fig, (p1, p2, p3) = plt.subplots(3, sharex = True)
    p1.plot(data[1][ticker]["Returns"], 'b', data[1][comp]["Returns"], 'r')
    p1.set(ylabel = "Returns")
    scaling_a = data[1][ticker]["close"][-0]
    scaling_b = data[1][comp]["close"][0]
    p2.plot((data[1][ticker]["close"]/scaling_a)*100, 
             'b', (data[1][comp]["close"]/scaling_b)*100, 'r')
    p2.set(ylabel="Prices")
    p2.legend((ticker, comp))
    p2.grid(True)
    vol_scale_a = data[1][ticker]["volume"].max() #[0]
    vol_scale_b = data[1][comp]["volume"].max() #[0]
    p3.plot((data[1][ticker]["volume"]/vol_scale_a)*100,'b',
             (data[1][comp]["volume"]/vol_scale_b)*100, 'r')
    p3.set(ylabel="Volume")
    fig.suptitle("Returns, price and volume of {0} (blue) vs {1} (red)".format(ticker,
                comp))
    fig.savefig(loc, dpi='figure')
    #https://matplotlib.org/tutorials/introductory/pyplot.html
    
def find_max(data):
    '''Returns date of the lowest and highest value of a list'''
    
    data = data.sort_values()
    index = {}
    index["Lowest"] = data.iloc[0]
    index["Highest"] = data.iloc[-1]
    index["LowestD"] = np.argmin(data)
    index["HighestD"] = np.argmax(data)
    return index
    
def data_of_top(collection, start, end):
    '''Returns return data and correlation for a collection of names'''
    
    top_healthcare = import_collections(collection)
    names = list(top_healthcare["Ticker"])
    names.append("SPY")
    stocks = import_multiple("Returns", names, start, end) #Returns a dataframe with daily returns
    stocks_corr = stocks[0].corr()
    stock_returns = ReturnData(stocks[0], start, end)
    price = get_price(stocks, names)
    stock_returns["Price"] = price
    print("The correlation, yearly mean return and plot of {0} is given below:".format(names))
    print("\nCorrelation\n")
    print(stocks_corr)
    print(stock_returns)
    stocks.append(stock_returns)
    return stocks

def main(plot = False, printit = False):
    end = datetime.today()
    start = end.replace(year=end.year-5) #Takes data from 5 years ago
    collections = ["Real Estate", "Energy", "Utilities", "Communication Services", 
                "Technology", "Industrials", "Healthcare"]
    #^the above works
    data = {}
    for i in range(len(collections)):
        data [collections[i]] = data_of_top(collections[i], start, end)
    #SPY_trailing = SPY["close"].rolling(window=20).mean()   

    tick = "MRK"
    if plot == True:
        create_plot(data["Healthcare"], tick, "Figure.pdf")
        lows = find_max(data["Healthcare"][1][tick]["Returns"])
        print('''{0} achieved its highest daily return on {1} at a return of {2}, its lowest on {3} at a return of {4}'''.format(tick, 
          lows["HighestD"].strftime("%m/%d/%Y"), lows["Highest"], lows["LowestD"].strftime("%m/%d/%Y"),
          lows["Lowest"]))
    if printit == True:
        for i in range(len(data)):
            path = "C:/Users/Sandsnes/Desktop/Stock project/"
            files = data[collections[i]][2]
            files.to_csv(path+collections[i]+".csv")
    #https://dash.plot.ly/getting-started
    
    #stock_return = df.apply(lambda x:x/x[0])
    #stocks.plot(grid = True) ###Plots the three datapoints
    #https://medium.com/python-data/capm-analysis-calculating-stock-beta-as-a-regression-in-python-c82d189db536
    #https://ntguardian.wordpress.com/2018/07/17/stock-data-analysis-python-v2/
    
    #Seaborn
    #scikit-learn, StatsModels
    
    
if __name__ == "__main__":
    main()