import pandas as pd

def merge_with_live(ohlc, stockData):
    latestData = {}
    for stock in stockData:
        if stock not in ohlc:
            continue
        
        if ohlc[stock]['DATE'][len(ohlc[stock].index)-1] == stockData[stock]['DATE']:
            latestData[stock] = ohlc[stock]
        else:
            dfA = ohlc[stock].drop('index', axis=1)
            dfB = pd.DataFrame([stockData[stock]])
            dfC = pd.concat([dfA, dfB], ignore_index=True)
            latestData[stock] = dfC

    return latestData
