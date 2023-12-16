import plotly.graph_objects as go

from utils import *
from plotly.subplots import make_subplots


class Indicator():
        
    def __init__(self, data, tickerName='', patternTitle=''):
        self.df = data
        self.window = getPivotWindow()
        self.tickerName = tickerName
        self.patternTitle = patternTitle
        self.emaWindow = getEMAWindow()


    def getFullCandleChart(self, candleIndex=None):
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
    