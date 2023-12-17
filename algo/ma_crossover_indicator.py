import talib
import streamlit as st
import pandas_ta as ta
import plotly.graph_objects as go

from .indicator import Indicator
from plotly.subplots import make_subplots
from utils import getChartHeight, getCandleCount, getPivotWindow
from .candlestick_patterns import getCandlestickPatterns


class MACrossoverIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.emaWindow)
        
        self.fib_seq = [50, 200]
        for num in self.fib_seq:
            self.df[f"EMA{num}"] = ta.ema(data.CLOSE, length=num)

    def drawEMA(self, fig, dfSlice):
        colors = ['red', 'yellow']

        i = 0
        for num in self.fib_seq:
            fig.add_scatter(x=dfSlice.index, y=dfSlice[f"EMA{num}"], line=dict(color=colors[i], width=1.5), name=f"EMA{num}", row=1, col=1)
            i += 1

        return fig


    def getIndicator(self, candleIndex):
        start = candleIndex-getCandleCount()
        if start < 0:
            start = 0
        dfSlice = self.df[start:candleIndex+1]

        patternTitle = self.patternTitle
            
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
               vertical_spacing=0.05, subplot_titles=(self.tickerName, patternTitle), 
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

        # draw EMA
        fig = self.drawEMA(fig=fig, dfSlice=dfSlice)

        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_showlegend=False)
        fig.update(layout_height=getChartHeight())
        # fig.update(layout_dragmode='drawline')
        return fig
        

    def getSignal(self, candleIndex):
        emas = [f"EMA{num}" for num in self.fib_seq]
            
        if self.df[emas[0]][candleIndex] > self.df[emas[1]][candleIndex]:
            if (self.df[emas[0]][candleIndex-1] <= self.df[emas[1]][candleIndex-1]):
                return 'BUY'
        elif self.df[emas[0]][candleIndex] < self.df[emas[1]][candleIndex]:
            if (self.df[emas[0]][candleIndex-1] >= self.df[emas[1]][candleIndex-1]):
                return 'SELL'

        return ''
    

    def getOrder(self, candleIndex):
        close = self.df.CLOSE[candleIndex]
        high = self.df.HIGH[candleIndex]
        prevHigh = self.df.HIGH[candleIndex-1]
        low = self.df.LOW[candleIndex]
        prevLow = self.df.LOW[candleIndex-1]
        
        atr = self.df.ATR[candleIndex]

        signal = self.getSignal(candleIndex=candleIndex)
        order = {
            "valid": False,
            "signal": signal,
            "candleIndex": candleIndex,
            "proximity": 0,
            "stop_loss": None,
            "target": None,
            "strike_price": close
        }
        
        if signal == 'BUY':
            order["valid"] = True
            order["stop_loss"] = round(min(low, prevLow) - atr, 2)
            order["target"] = close + 2*(close - order["stop_loss"])
        elif signal == 'SELL':
            order["valid"] = True
            order["stop_loss"] = round(max(high, prevHigh) + atr, 2)
            order["target"] = close - 2*(order["stop_loss"] - close)
            
        return order