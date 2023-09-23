import talib
import numpy as np
import plotly.graph_objects as go

from .indicator import Indicator
from plotly.subplots import make_subplots
from utils import getPivotWindow, getCandleCount, getChartHeight


class TrendlineIndicator(Indicator):

    def __init__(self, data, tickerName='', patternTitle=''):
        Indicator.__init__(self, data=data, tickerName=tickerName, patternTitle=patternTitle)
        self.df["ATR"] = talib.ATR(data.HIGH, data.LOW, data.CLOSE, timeperiod=self.window)


    def drawTrendline(self, fig, dfSlice):
        supports = dfSlice[dfSlice.LOW == dfSlice.LOW.rolling(self.window, center=True).min()]
        resistances = dfSlice[dfSlice.HIGH == dfSlice.HIGH.rolling(self.window, center=True).max()]
        proxLCTR = proxHCTR = proxLCTS = proxHCTS = 999
        mresistance = msupport = supp = resis = None
        low = dfSlice.LOW.tolist()[-1]
        high = dfSlice.HIGH.tolist()[-1]

        x = np.array(range(dfSlice.index.start, dfSlice.index.stop))
        if len(resistances.index.tolist()) > 1:
            mresistance, cresistance = np.polyfit(resistances.index.tolist(), resistances.HIGH.tolist(), 1)
            fig.add_trace(go.Scatter(x=x, y=mresistance*x + cresistance, line=dict(color="red", width=1), mode="lines", name="resistance trendline"))
            # fig.add_scatter(x=resistances.index, y=resistances.HIGH, mode="markers",
            #             marker=dict(size=7, color="red"),
            #             name="pivot")
            
            resis = mresistance*x[-1] + cresistance
            proxLCTR = round(abs(low-resis)*100/resis, 2)
            proxHCTR = round(abs(high-resis)*100/resis, 2)

        if len(supports.index.tolist()) > 1:
            msupport, csupport = np.polyfit(supports.index.tolist(), supports.LOW.tolist(), 1)
            fig.add_trace(go.Scatter(x=x, y=msupport*x + csupport, line=dict(color="yellow", width=1), mode="lines", name="support trendline"))
            # fig.add_scatter(x=supports.index, y=supports.LOW, mode="markers",
            #             marker=dict(size=7, color="yellow"),
            #             name="pivot")
            supp = msupport*x[-1] + csupport
            proxLCTS = round(abs(low-supp)*100/supp, 2)
            proxHCTS = round(abs(high-supp)*100/supp, 2)

        self.proximity = min(proxLCTR, proxHCTR, proxLCTS, proxHCTS)

        return fig
    

    def getOrder(self, candleIndex):
        start = candleIndex-getCandleCount()
        if start < 0:
            start = 0
        dfSlice = self.df[start:candleIndex+1]
    
        supports = dfSlice[dfSlice.LOW == dfSlice.LOW.rolling(self.window, center=True).min()]
        resistances = dfSlice[dfSlice.HIGH == dfSlice.HIGH.rolling(self.window, center=True).max()]
        proxLCTR = proxHCTR = proxLCTS = proxHCTS = 999
        atr = dfSlice.ATR[candleIndex]

        open = dfSlice.OPEN[candleIndex]
        high = dfSlice.HIGH[candleIndex]
        low = dfSlice.LOW[candleIndex]
        close = dfSlice.CLOSE[candleIndex]

        x = np.array(range(dfSlice.index.start, dfSlice.index.stop))
        if len(resistances.index.tolist()) > 1:
            mresistance, cresistance = np.polyfit(resistances.index.tolist(), resistances.HIGH.tolist(), 1)
            resis = mresistance*x[-1] + cresistance
            proxLCTR = round(abs(low-resis)*100/resis, 2)
            proxHCTR = round(abs(high-resis)*100/resis, 2)

        if len(supports.index.tolist()) > 1:
            msupport, csupport = np.polyfit(supports.index.tolist(), supports.LOW.tolist(), 1)
            supp = msupport*x[-1] + csupport
            proxLCTS = round(abs(low-supp)*100/supp, 2)
            proxHCTS = round(abs(high-supp)*100/supp, 2)

        self.proximity = min(proxLCTR, proxHCTR, proxLCTS, proxHCTS)

        order = {
            "valid": False,
            "candleIndex": candleIndex,
            "proximity": self.proximity,
            "stop_loss": None,
            "target": None,
            "strike_price": close
        }

        # proximity threshold
        if self.proximity > 0.5:
            return order
        
        if self.proximity == proxLCTR:
            if mresistance < 0:
                if close > open:
                    stop_loss = round(low - 1.5*atr, 2)
                    target = round(close + 1.5*(close-stop_loss), 2)
                    order["valid"] = True
                    order["signal"] = 'BUY'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
            else:
                if close > open:
                    stop_loss = round(low - 1.5*atr, 2)
                    target = round(close + 1.5*(close-stop_loss), 2)
                    order["valid"] = True
                    order["signal"] = 'BUY'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
            
        elif self.proximity == proxHCTR:
            if mresistance < 0:
                if open > close:
                    stop_loss = round(high + 1.5*atr, 2)
                    target = round(close - 1.5*(stop_loss-close), 2)
                    order["valid"] = True
                    order["signal"] = 'SELL'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
            else:
                if open > close:
                    stop_loss = round(high + 1.5*atr, 2)
                    target = round(close - 1.5*(stop_loss-close), 2)
                    order["valid"] = True
                    order["signal"] = 'SELL'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
            
        elif self.proximity == proxLCTS:
            if msupport < 0:
                if close > open:
                    stop_loss = round(low - 1.5*atr, 2)
                    target = round(close + 1.5*(close-stop_loss), 2)
                    order["valid"] = True
                    order["signal"] = 'BUY'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
            else:
                if close > open:
                    stop_loss = round(low - 1.5*atr, 2)
                    target = round(close + 1.5*(close-stop_loss), 2)
                    order["valid"] = True
                    order["signal"] = 'BUY'
                    order["stop_loss"] = stop_loss
                    order["target"] = target

        elif self.proximity == proxHCTS:
            if msupport < 0:
                if open > close:
                    stop_loss = round(high + 1.5*atr, 2)
                    target = round(close - 1.5*(stop_loss-close), 2)
                    order["valid"] = True
                    order["signal"] = 'SELL'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
            else:
                if open > close:
                    stop_loss = round(high + 1.5*atr, 2)
                    target = round(close - 1.5*(stop_loss-close), 2)
                    order["valid"] = True
                    order["signal"] = 'SELL'
                    order["stop_loss"] = stop_loss
                    order["target"] = target
                
        return order

    
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

        # draw trendlines
        fig = self.drawTrendline(fig=fig, dfSlice=dfSlice)
            
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_showlegend=False)
        fig.update(layout_height=getChartHeight())
        # fig.update(layout_dragmode='drawline')
        return fig
        