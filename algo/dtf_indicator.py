import math
import talib
import numpy as np
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go

from itertools import compress
from .indicator import Indicator
from plotly.subplots import make_subplots
from .candlestick_patterns import getCandlestickPatterns
from utils import getCandleCount, getChartHeight, getFilterBySetting


class DTFIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.patterns = getFilterBySetting()
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.window)
        hdf = yf.download(f"{tickerName}.NS", interval='1h', period='2mo', progress=False)
        hdf.rename(columns={'Open': 'OPEN', 'High': 'HIGH','Low': 'LOW', 'Close': 'CLOSE', 'Volume': 'VOLUME'}, inplace=True)
        
        self.dosc = ta.stoch(high=data.HIGH, low=data.LOW, close=data.CLOSE, k=21, d=5)
        self.hosc = ta.stoch(high=hdf.HIGH, low=hdf.LOW, close=hdf.CLOSE, k=21, d=5)
        self.hosc.insert(loc=0, column='DATE', value=self.hosc.index)
        self.hosc['DATE'] = pd.to_datetime(self.hosc.DATE).dt.date


    def getLevels(self, candleIndex):
        dfSlice = self.df[0:candleIndex+1]
        supports = dfSlice[dfSlice.LOW == dfSlice.LOW.rolling(self.window, center=True).min()].LOW
        resistances = dfSlice[dfSlice.HIGH == dfSlice.HIGH.rolling(self.window, center=True).max()].HIGH
        levels = pd.concat([supports, resistances])
        
        filteredLevels = []
        sortedLevels = levels.sort_values(ascending=True).to_list()
        for i in range(len(sortedLevels)-1):
            currentLevel = sortedLevels[i]            
            upperLevel = sortedLevels[i+1]

            proximity = round((upperLevel - currentLevel)*100/upperLevel, 2)
            if proximity < 0.5:
                filteredLevels.append(currentLevel)

        return filteredLevels
    

    def drawLevels(self, fig, dfSlice, candleIndex):
        levels = self.getLevels(candleIndex)

        # for better visuals
        minLevel = min(dfSlice.LOW) - dfSlice.ATR[candleIndex]
        maxLevel = max(dfSlice.HIGH) + dfSlice.ATR[candleIndex]
        levels = [level for level in levels if level > minLevel and level < maxLevel]
        # ------------------

        # draw levels
        for level in levels:
            fig.add_shape(
                type='line',
                x0=dfSlice.index.start - 2,
                y0=level,
                x1=dfSlice.index.stop + 2,
                y1=level,
                line=dict(color="#38527a"),
                xref='x',
                yref='y',
                layer='below',
                row= 1,
                col=1
            )

        return fig


    def getIndicator(self, candleIndex):
        start = candleIndex-getCandleCount()
        if start < 0:
            start = 0
        dfSlice = self.df[start:candleIndex+1]
        
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
               vertical_spacing=0.05, subplot_titles=(self.tickerName, '-'), 
               row_width=[0.25, 0.05, 0.7])
        
        
        # draw candlestick
        fig.add_trace(go.Candlestick(x=dfSlice.index,
                                open=dfSlice.OPEN,
                                high=dfSlice.HIGH,
                                low=dfSlice.LOW,
                                close=dfSlice.CLOSE), row=1, col=1)
        
        # plot volume
        if 'VOLUME' in dfSlice:
            fig.add_trace(go.Bar(x=dfSlice.index, y=dfSlice.VOLUME, showlegend=False), row=2, col=1)
        
        fig.add_trace(go.Scatter(
                x=self.dosc.loc[start:candleIndex+1].index,
                y=self.dosc['STOCHk_21_5_3'].loc[start:candleIndex+1],
                line=dict(color='red', width=2),
                name='fast',
            ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
                x=self.dosc.loc[start:candleIndex+1].index,
                y=self.dosc['STOCHd_21_5_3'].loc[start:candleIndex+1],
                line=dict(color='yellow', width=2),
                name='slow',
            ), row=3, col=1)
        # draw levels
        fig = self.drawLevels(fig=fig, dfSlice=dfSlice, candleIndex=candleIndex)

        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_showlegend=False)
        fig.update(layout_height=getChartHeight())
        # fig.update(layout_dragmode='drawline')
        return fig
    

    def getSignal(self, candleIndex):
        prevDate = self.df.DATE[candleIndex-1]
        curDate = self.df.DATE[candleIndex]

        prevhourlyDateData = self.hosc[self.hosc.DATE == prevDate]
        curhourlyDateData = self.hosc[self.hosc.DATE == curDate]
        
        k = prevhourlyDateData['STOCHk_21_5_3'].tolist()[-1:]
        d = prevhourlyDateData['STOCHd_21_5_3'].tolist()[-1:]
        k.extend(curhourlyDateData['STOCHk_21_5_3'].tolist())
        d.extend(curhourlyDateData['STOCHd_21_5_3'].tolist())
        
        globalk = self.dosc['STOCHk_21_5_3'][candleIndex]
        globald = self.dosc['STOCHd_21_5_3'][candleIndex]

        global_momentum = 0
        if globalk > globald:
            global_momentum = 1
        elif globalk < globald:
            global_momentum = -1


        local_momentum = 0
        for i in range(len(k)-1):
            if k[i] < d[i] and k[i+1] > d[i+1]:
                local_momentum = 1
            elif k[i] > d[i] and k[i+1] < d[i+1]:
                local_momentum = -1

        if  global_momentum == local_momentum:
            if local_momentum == 1:
                return 'BUY' 
            elif local_momentum == -1:
                return 'SELL'

        
    def getOrder(self, candleIndex):
        low = self.df.LOW[candleIndex]
        high = self.df.HIGH[candleIndex]
        close = self.df.CLOSE[candleIndex]

        atr = self.df.ATR[candleIndex]
        
        order = {
            "valid": False,
            "signal": "",
            "candleIndex": candleIndex,
            "proximity": None,
            "stop_loss": None,
            "target": None,
            "strike_price": close
        }

        signal = self.getSignal(candleIndex=candleIndex)        
        
        if signal == 'BUY':
            order["valid"] = True
            order["signal"] = signal
            order["stop_loss"] = close - atr
            order["target"] = close + 2*(close - order["stop_loss"])
        elif signal == 'SELL':
            order["valid"] = True
            order["signal"] = signal
            order["stop_loss"] = close + atr
            order["target"] = close - 2*(order["stop_loss"] - close)
        
        return order