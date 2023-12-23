import math
import talib
import numpy as np
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

from itertools import compress
from .indicator import Indicator
from plotly.subplots import make_subplots
from .candlestick_patterns import getCandlestickPatterns
from utils import getCandleCount, getChartHeight, getFilterBySetting


class MorningStarIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.patterns = getFilterBySetting()
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.window)

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
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
               vertical_spacing=0.05, subplot_titles=(self.tickerName, '-'), 
               row_width=[0.2, 0.7])
        
        # draw candlestick
        fig.add_trace(go.Candlestick(x=dfSlice.index,
                                open=dfSlice.OPEN,
                                high=dfSlice.HIGH,
                                low=dfSlice.LOW,
                                close=dfSlice.CLOSE), row=1, col=1)
        
        # plot volume
        if 'VOLUME' in dfSlice:
            fig.add_trace(go.Bar(x=dfSlice.index, y=dfSlice.VOLUME, showlegend=False), row=2, col=1)

        # draw levels
        fig = self.drawLevels(fig=fig, dfSlice=dfSlice, candleIndex=candleIndex)

        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_showlegend=False)
        fig.update(layout_height=getChartHeight())
        # fig.update(layout_dragmode='drawline')
        return fig
    

    def getSignal(self, candleIndex):
        # bullish ( start of reversal )
        curopen = self.df.OPEN[candleIndex]
        curclose = self.df.CLOSE[candleIndex]
        
        # bearish
        pprevopen = self.df.OPEN[candleIndex-2]
        pprevclose = self.df.CLOSE[candleIndex-2]
        
        # doji
        prevopen = self.df.OPEN[candleIndex-1]
        prevhigh = self.df.HIGH[candleIndex-1]
        prevlow = self.df.LOW[candleIndex-1]
        prevclose = self.df.CLOSE[candleIndex-1]
    
        # print((abs(prevopen-prevclose)*100)/prevclose)

        if curclose < prevhigh:
            return ''
        elif pprevopen < pprevclose or curopen > curclose:
            return ''
        elif self.df.VOLUME[candleIndex] < self.df.VOLUME[candleIndex-1]:
            return ''
        elif (abs(prevopen-prevclose)*100)/prevclose > 0.5:
            return '' 
        elif prevopen > min(self.df.CLOSE[candleIndex-6:candleIndex-1]) or prevlow > min(self.df.LOW[candleIndex-6:candleIndex-1]):
            return ''
        
        return 'BUY'


    def getOrder(self, candleIndex):
        high = self.df.HIGH[candleIndex]
        low = self.df.LOW[candleIndex]
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
            order["stop_loss"] = low - atr
            order["target"] = round(close + 2*(abs(close - order["stop_loss"])), 2)
        elif signal == 'SELL':
            order["valid"] = True
            order["signal"] = signal
            order["stop_loss"] = high + atr
            order["target"] = round(close - 2*(abs(close - order["stop_loss"])), 2)
        
        return order