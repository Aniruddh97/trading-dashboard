import math
import talib
import numpy as np
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

from .indicator import Indicator
from plotly.subplots import make_subplots
from utils import getPivotWindow, getCandleCount, getChartHeight


class SupportResistanceIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.window)
        self.df["SMA200"] = talib.SMA(data.CLOSE, timeperiod=200)

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
    
    
    def drawSMA(self, fig, dfSlice):
        fig.add_scatter(x=dfSlice.index, y=dfSlice.SMA200, line=dict(color="aliceblue", width=0.25), name="200 SMA", row=1, col=1),
        return fig

    
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

        # draw levels
        fig = self.drawLevels(fig=fig, dfSlice=dfSlice, candleIndex=candleIndex)

        # draw sma
        fig = self.drawSMA(fig=fig, dfSlice=dfSlice)

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
        order = {
            "valid": False,
            "signal": "",
            "candleIndex": candleIndex,
            "proximity": None,
            "stop_loss": None,
            "target": None,
            "strike_price": close
        }
        
        supports = []
        resistances = []
        levels = self.getLevels(candleIndex=candleIndex)
        for level in levels:
            if level > high:
                resistances.append(level)
            elif level < low:
                supports.append(level)

        atr = self.df.ATR[candleIndex]
        proximityThreshold = 0.75

        if len(supports) > 0:
            closestSupport = max(supports)
            proximitySupport = (abs(low - closestSupport))*100/low
            if close > open and proximitySupport < proximityThreshold:
                order["valid"] = True
                order["signal"] = 'BUY'
                order["stop_loss"] = closestSupport - atr
                order["target"] = round(close + 2*(abs(close - order["stop_loss"])), 2)
                order["proximity"] = proximitySupport
        
        if len(resistances) > 0:
            closestResistance = min(resistances)
            proximityResistance = (abs(closestResistance - high))*100/closestResistance
            if open > close and proximityResistance < proximityThreshold:
                order["valid"] = True
                order["signal"] = 'SELL'
                order["stop_loss"] = closestResistance + atr
                order["target"] = round(close - 2*(abs(close - order["stop_loss"])), 2)
                order["proximity"] = proximityResistance

        return order