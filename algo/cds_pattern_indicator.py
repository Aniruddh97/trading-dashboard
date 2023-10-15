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


class CandlestickPatternIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.patterns = getFilterBySetting()
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.window)

        df = self.df
        op = df['OPEN'].astype(float)
        lo = df['LOW'].astype(float)
        hi = df['HIGH'].astype(float)
        cl = df['CLOSE'].astype(float)

        candlePatterns = talib.get_function_groups()['Pattern Recognition']
        for candle in candlePatterns:
            df[candle] = getattr(talib, candle)(op, hi, lo, cl)
        
        self.patternDict = {}
        for index, row in df.iterrows():
            patterns = list(compress(row[candlePatterns].keys(), row[candlePatterns].values != 0))
            container = []
            for pattern in patterns:
                if row[pattern] > 0:
                    container.append(pattern + '_Bull')
                else:
                    container.append(pattern + '_Bear')

            self.patternDict[index] = container


    def getIndicator(self, candleIndex):
        start = candleIndex-getCandleCount()
        if start < 0:
            start = 0
        dfSlice = self.df[start:candleIndex+1]

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
               vertical_spacing=0.05, subplot_titles=(self.tickerName, self.patternTitle), 
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

        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_showlegend=False)
        fig.update(layout_height=getChartHeight())
        # fig.update(layout_dragmode='drawline')
        return fig
    

    def getOrder(self, candleIndex):
        open = self.df.OPEN[candleIndex]
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

        if len(self.patterns) == 0:
            return order
        
        currentPatterns = self.patternDict[candleIndex]
        if len(currentPatterns) > 0 and set(self.patterns).issubset(set(currentPatterns)):
            if 'Bull' in self.patterns[0]:
                order["valid"] = True
                order["signal"] = 'BUY'
                order["stop_loss"] = low - atr
                order["target"] = round(close + 2*(abs(close - order["stop_loss"])), 2)
            else:
                order["valid"] = True
                order["signal"] = 'SELL'
                order["stop_loss"] = high + atr
                order["target"] = round(close - 2*(abs(close - order["stop_loss"])), 2)

        return order