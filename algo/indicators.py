import math
import numpy as np
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

from utils import getPivotWindow, getCandleCount, getChartHeight, getIndicatorSetting
from plotly.subplots import make_subplots


class SupportResistanceIndicator:

    def __init__(self, data, window=31, backCandles=5, tickerName='', patternTitle=''):
        self.window = getPivotWindow()
        self.backCandles = backCandles
        self.df = data
        self.tickerName = tickerName
        self.patternTitle = patternTitle
        self.RRR = 1.5
        # self.df['RSI'] = ta.rsi(data.CLOSE, length=14)
        # self.df['Level'] = 0

        # candle proximity with a level
        self.proximity = (data.HIGH.mean()-data.LOW.mean()) / 4
        # proximity b/w levels
        self.levelProximity = max(data.HIGH)/100


    def getLevels(self, candleIndex):
        dfSlice = self.df[0:candleIndex+1]
        supports = dfSlice[dfSlice.LOW == dfSlice.LOW.rolling(self.window, center=True).min()].LOW
        resistances = dfSlice[dfSlice.HIGH == dfSlice.HIGH.rolling(self.window, center=True).max()].HIGH
        levels = pd.concat([supports, resistances])
        return levels
        # return levels[abs(levels.diff()) > self.levelProximity]

    
    def drawEMA(self, fig, dfSlice):
        dfSlice["EMAA"] = ta.ema(dfSlice.CLOSE, length=5)
        dfSlice["EMAB"] = ta.ema(dfSlice.CLOSE, length=8)
        dfSlice["EMAC"] = ta.ema(dfSlice.CLOSE, length=13)

        fig.add_scatter(x=dfSlice.index, y=dfSlice.EMAA, line=dict(color="orange", width=2.25), name="EMAA", row=1, col=1),
        fig.add_scatter(x=dfSlice.index, y=dfSlice.EMAB, line=dict(color="yellow", width=2.25), name="EMAB", row=1, col=1),
        fig.add_scatter(x=dfSlice.index, y=dfSlice.EMAC, line=dict(color="cornflowerblue", width=2.25), name="EMAC", row=1, col=1),

        return fig
    

    def drawLevels(self, fig, dfSlice, candleIndex):
        levels = self.getLevels(candleIndex)

        # for better visuals
        levels = levels[levels > (min(dfSlice.CLOSE) - self.levelProximity)]
        levels = levels[levels < (max(dfSlice.HIGH) + self.levelProximity)]
        # ------------------

        # draw levels
        for level in levels.to_list():
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
    

    def createOrder(self, candleIndex, stop_loss, target, strike_price):
        return {
            "valid": True,
            "candleIndex": candleIndex,
            "proximity": self.proximity,
            "stop_loss": stop_loss,
            "target": target,
            "strike_price": strike_price
        }


    def getOrder(self, candleIndex):
        start = candleIndex-getCandleCount()
        if start < 0:
            start = 0
        dfSlice = self.df[start:candleIndex+1]
    
        supports = dfSlice[dfSlice.LOW == dfSlice.LOW.rolling(self.window, center=True).min()]
        resistances = dfSlice[dfSlice.HIGH == dfSlice.HIGH.rolling(self.window, center=True).max()]
        proxLCTR = proxHCTR = proxLCTS = proxHCTS = 999
        low = dfSlice.LOW[candleIndex]
        high = dfSlice.HIGH[candleIndex]

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
            "proximity": self.proximity,
        }

        # proximity threshold
        if self.proximity > 1:
            return order
        
        data = dfSlice.tail(1).to_dict('records')[-1]
        if self.proximity == proxLCTR:

            if mresistance < 0:
                if data['CLOSE'] > data['OPEN']:
                    stop_loss = round(mresistance*(x[-1]+5) + cresistance, 2)
                    target = round(data['CLOSE'] + 1.5*(data['CLOSE']-stop_loss), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
            else:
                if data['CLOSE'] > data['OPEN']:
                    stop_loss = mresistance*(x[-1]-5) + cresistance
                    target = round(data['CLOSE'] + 1.5*(data['CLOSE']-stop_loss), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
            
        elif self.proximity == proxHCTR:

            if mresistance < 0:
                if data['OPEN'] > data['CLOSE']:
                    stop_loss = mresistance*(x[-1]-5) + cresistance
                    target = round(data['CLOSE'] - 1.5*(stop_loss-data['CLOSE']), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
            else:
                if data['OPEN'] > data['CLOSE']:
                    stop_loss = mresistance*(x[-1]-5) + cresistance
                    target = round(data['CLOSE'] - 1.5*(stop_loss-data['CLOSE']), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
            
        elif self.proximity == proxLCTS:

            if msupport < 0:
                if data['CLOSE'] > data['OPEN']:
                    stop_loss = round(msupport*(x[-1]+5) + csupport, 2)
                    target = round(data['CLOSE'] + 1.5*(data['CLOSE']-stop_loss), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
            else:
                if data['CLOSE'] > data['OPEN']:
                    stop_loss = msupport*(x[-1]-5) + csupport
                    target = round(data['CLOSE'] + 1.5*(data['CLOSE']-stop_loss), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )

        elif self.proximity == proxHCTS:

            if msupport < 0:
                if data['OPEN'] > data['CLOSE']:
                    stop_loss = msupport*(x[-1]-5) + csupport
                    target = round(data['CLOSE'] - 1.5*(stop_loss-data['CLOSE']), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
            else:
                if data['OPEN'] > data['CLOSE']:
                    stop_loss = msupport*(x[-1]+5) + csupport
                    target = round(data['CLOSE'] - 1.5*(stop_loss-data['CLOSE']), 2)
                    return self.createOrder(
                        candleIndex=candleIndex, 
                        stop_loss=stop_loss,
                        target=target,
                        strike_price=data['CLOSE']
                    )
                
        return order


    def isCloseToResistance(self, candleIndex, levels):
        if len(levels)==0:
            return 0
        minLevel = min(levels, key=lambda x:abs(x-self.df.HIGH[candleIndex]))
        c1 = abs(self.df.HIGH[candleIndex]-minLevel)<=self.proximity
        c2 = abs(max(self.df.OPEN[candleIndex],self.df.CLOSE[candleIndex])-minLevel)<=self.proximity
        c3 = min(self.df.OPEN[candleIndex],self.df.CLOSE[candleIndex])<minLevel
        c4 = self.df.LOW[candleIndex]<minLevel
        c5 = self.df.CLOSE[candleIndex] > min(self.df.CLOSE[candleIndex-self.backCandles:candleIndex-1])
        if( (c1 or c2) and c3 and c4 and c5):
            return minLevel
        else:
            return 0
    
    
    def isCloseToSupport(self, candleIndex, levels):
        if len(levels)==0:
            return 0
        minLevel = min(levels, key=lambda x:abs(x-self.df.LOW[candleIndex]))
        c1 = abs(self.df.LOW[candleIndex]-minLevel)<=self.proximity
        c2 = abs(min(self.df.OPEN[candleIndex],self.df.CLOSE[candleIndex])-minLevel)<=self.proximity
        c3 = max(self.df.OPEN[candleIndex],self.df.CLOSE[candleIndex])>minLevel
        c4 = self.df.HIGH[candleIndex]>minLevel
        c5 = self.df.CLOSE[candleIndex] < max(self.df.CLOSE[candleIndex-self.backCandles:candleIndex-1])
        if( (c1 or c2) and c3 and c4 and c5):
            return minLevel
        else:
            return 0
        

    def arePrevCandlesBelowResistance(self, candleIndex, level):
        return self.df.loc[candleIndex-self.backCandles:candleIndex-1, 'High'].max() < level


    def arePrevCandlesAboveSupport(self, candleIndex, level):
        return self.df.loc[candleIndex-self.backCandles:candleIndex-1, 'Low'].min() > level  


    def getCandleSignal(self, candleIndex):
        levels = self.getLevels(candleIndex)

        cR = self.isCloseToResistance(candleIndex, levels)
        cS = self.isCloseToSupport(candleIndex, levels)

        if (cR and self.arePrevCandlesBelowResistance(candleIndex, cR) and self.df.RSI[candleIndex-1:candleIndex].min()<45 ):#and df.RSI[l]>65
            self.df.loc[candleIndex, 'Level'] = cR
            return 1
        elif(cS and self.arePrevCandlesAboveSupport(candleIndex, cS) and self.df.RSI[candleIndex-1:candleIndex].max()>55 ):#and df.RSI[l]<35
            self.df.loc[candleIndex, 'Level'] = cS
            return 2
        else:
            return 0
        
    
    def getCandleChart(self, candleIndex=None):
        if not candleIndex:
            candleIndex = self.df.index.stop-1

        dfSlice = self.df[0:candleIndex+1]

        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            subplot_titles=(self.tickerName, self.patternTitle), 
            row_width=[0.2, 0.7]
        )
        
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
        return fig


    def getIndicator(self, candleIndex):
        start = candleIndex-getCandleCount()
        if start < 0:
            start = 0
        dfSlice = self.df[start:candleIndex+1]

        patternTitle = self.patternTitle
        if 'candlestick_pattern' in dfSlice:
            patternTitle = dfSlice['candlestick_pattern'][dfSlice.index.stop-1][3:].lower()
            
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

        # draw EMAS
        ind = getIndicatorSetting()

        if 'EMA' in ind:
            fig = self.drawEMA(fig=fig, dfSlice=dfSlice)
        
        # draw levels
        if 'S&R' in ind:
            fig = self.drawLevels(fig=fig, dfSlice=dfSlice, candleIndex=candleIndex)

        # draw trendlines
        if 'Trendline' in ind:
            fig = self.drawTrendline(fig=fig, dfSlice=dfSlice)
            
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_showlegend=False)
        fig.update(layout_height=getChartHeight())
        # fig.update(layout_dragmode='drawline')
        return fig
        
    
    def getSignalMarker(self, x):
        markerDistance = (x["High"]-x["Low"])/10
        if x["Signal"]==2:
            return x["Low"]-markerDistance
        elif x["Signal"]==1:
            return x["High"]+markerDistance
        else:
            return np.nan
        

    def setSignalMarker(self):
        self.df["SignalMarker"] = [self.getSignalMarker(row) for index, row in self.df.iterrows()]

    
    def calculate(self, all=True):
        self.setSignal(all)
        self.setSignalMarker()
        self.setTarget()
        self.setStoploss()


    def getSignal(self, all=True):
        if all:
            return [self.getCandleSignal(index) for index in self.df.index]
        return [self.getCandleSignal(index) if index == len(self.df.index)-1 else 0 for index in self.df.index]
        

    def setSignal(self, all=True):
        self.df["Signal"] = self.getSignal(all)


    def getBuySell(self):
        return ["SELL" if row.Signal == 1 else "BUY" if row.Signal == 2 else "" for index, row in self.df.iterrows()]
    

    def getTarget(self, candleIndex):
        if self.df['Signal'][candleIndex] == 2:
            support = self.df['Level'][candleIndex]
            sl = support - self.proximity
            return self.df.CLOSE[candleIndex] + abs(self.df.CLOSE[candleIndex]-sl)*self.RRR
        elif self.df['Signal'][candleIndex] == 1:
            resistance = self.df['Level'][candleIndex]
            sl = resistance + self.proximity
            return self.df.CLOSE[candleIndex] - abs(self.df.CLOSE[candleIndex]-sl)*self.RRR
        else:
            return np.nan
    

    def setTarget(self):
        self.df['Target'] = [self.getTarget(index) for index in self.df.index]


    def getStoploss(self, candleIndex):
        if self.df['Signal'][candleIndex] == 2:
            return self.df['Level'][candleIndex] - (2*self.proximity)
        elif self.df['Signal'][candleIndex] == 1:
            return self.df['Level'][candleIndex] + (2*self.proximity)
        else:
            return np.nan
        
    
    def setStoploss(self):
        self.df['Stoploss'] = [self.getStoploss(index) for index in self.df.index]