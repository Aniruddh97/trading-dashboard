from utils import *
from .snr_indicator import *
from .trendline_indicator import *
from .cds_pattern_indicator import *
from .experimental_indicator import *
from .ma_crossover_indicator import *
from .moving_average_indicator import *
from .harami_breakout_indicator import *

def getIndicators(data, ticker='', pattern=''):
    indicatorSetting = getIndicatorSetting()
    indicators = []

    if 'S&R' in indicatorSetting:
        indicators.append(SupportResistanceIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'EMA' in indicatorSetting:
        indicators.append(MovingAverageIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'MACrossover' in indicatorSetting:
        indicators.append(MACrossoverIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'HaramiBreakout' in indicatorSetting:
        indicators.append(HaramiBreakoutIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'Experimental' in indicatorSetting:
        indicators.append(ExperimentalIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'Trendline' in indicatorSetting:
        indicators.append(TrendlineIndicator(data=data, tickerName=ticker, patternTitle=pattern))
    
    if 'CandlestickPattern' in indicatorSetting:
        indicators.append(CandlestickPatternIndicator(data=data, tickerName=ticker, patternTitle=pattern))

    # default
    if len(indicators) == 0:
        indicators.append(SupportResistanceIndicator(data=data, tickerName=ticker, patternTitle=pattern))

    return indicators