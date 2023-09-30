from utils import *
from .snr_indicator import *
from .trendline_indicator import *
from .moving_average_indicator import *

def getIndicators(data, ticker='', pattern=''):
    indicatorSetting = getIndicatorSetting()
    indicators = []

    if 'S&R' in indicatorSetting:
        indicators.append(SupportResistanceIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'EMA' in indicatorSetting:
        indicators.append(MovingAverageIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'Trendline' in indicatorSetting:
        indicators.append(TrendlineIndicator(data=data, tickerName=ticker, patternTitle=pattern))

    # default
    if len(indicators) == 0:
        indicators.append(SupportResistanceIndicator(data=data, tickerName=ticker, patternTitle=pattern))

    return indicators