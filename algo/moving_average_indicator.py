import talib
import streamlit as st
import pandas_ta as ta
import plotly.graph_objects as go

from .indicator import Indicator
from plotly.subplots import make_subplots
from utils import getChartHeight, getCandleCount, getPivotWindow
from .candlestick_patterns import getCandlestickPattern


class MovingAverageIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.df["EMA"] = ta.ema(data.CLOSE, length=self.window)
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.window)


    def drawEMA(self, fig, dfSlice):
        fig.add_scatter(x=dfSlice.index, y=dfSlice.EMA, line=dict(color="yellow", width=2), name="EMA", row=1, col=1),
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
        open = self.df.OPEN[candleIndex]
        high = self.df.HIGH[candleIndex]
        low = self.df.LOW[candleIndex]
        close = self.df.CLOSE[candleIndex]
        ema = self.df.EMA[candleIndex]
        prevVolume = self.df.VOLUME[candleIndex-1]
        volume = self.df.VOLUME[candleIndex]
        # patterns = getCandlestickPattern(df=self.df, candleIndex=candleIndex)
        # st.dataframe(patterns)
        proximityLow = round((abs(low-ema)/ema)*100, 2)
        proximityHigh = round((abs(high-ema)/ema)*100, 2)
        proximity = min(proximityHigh, proximityLow)
        self.proximity = proximity

        # set proximity threshold
        proximityThreshold = 0.5

        # bullish_patterns = ['CDLHAMMER_Bull', 'CDLENGULFING_Bull', 'CDLHARAMI_Bull', 'CDLCLOSINGMARUBOZU_Bull', 'CDLMARUBOZU_Bull']
        if close > open and proximityLow < proximityThreshold and volume > prevVolume:
            return 'BUY'
        
        # bearish_patterns = ['CDLINVERTEDHAMMER_Bear', 'CDLENGULFING_Bear', 'CDLHARAMI_Bear', 'CDLCLOSINGMARUBOZU_Bear', 'CDLMARUBOZU_Bear']
        if open > close and proximityHigh < proximityThreshold and volume > prevVolume:
            return 'SELL'
        
        return ''
    

    def getOrder(self, candleIndex):
        close = self.df.CLOSE[candleIndex]
        ema = self.df.EMA[candleIndex]
        atr = self.df.ATR[candleIndex]
        volume = self.df.VOLUME[candleIndex]
        prevVolume = self.df.VOLUME[candleIndex-1]

        signal = self.getSignal(candleIndex=candleIndex)
        order = {
            "valid": False,
            "signal": signal,
            "candleIndex": candleIndex,
            "proximity": self.proximity,
            "stop_loss": None,
            "target": None,
            "strike_price": close
        }
        
        if signal == 'BUY' and volume > prevVolume:
            order["valid"] = True
            order["stop_loss"] = round(ema - 1.5*atr, 2)
            order["target"] = close + 1.5 * (close - order["stop_loss"])
        elif signal == 'SELL' and volume > prevVolume:
            order["valid"] = True
            order["stop_loss"] = round(ema + 1.5*atr, 2)
            order["target"] = close - 1.5 * (order["stop_loss"] - close)
            
        return order