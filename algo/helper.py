from utils import *
from .snr_indicator import *
from .dtf_indicator import *
from .trendline_indicator import *
from .cds_pattern_indicator import *
from .eveningstar_indicator import *
from .morningstar_indicator import *
from .experimental_indicator import *
from .ma_crossover_indicator import *
from .moving_average_indicator import *
from .harami_breakout_indicator import *

ind_dic = {
    'S&R': SupportResistanceIndicator,
    'EMA': MovingAverageIndicator,
    'MACrossover': MACrossoverIndicator,
    'HaramiBreakout': HaramiBreakoutIndicator,
    'MorningStar': MorningStarIndicator,
    'EveningStar': EveningStarIndicator,
    'Experimental': ExperimentalIndicator,
    'CandlestickPattern': CandlestickPatternIndicator,
    'Trendline': TrendlineIndicator,
    'DTF': DTFIndicator,
}

def getIndicators(data, ticker='', pattern=''):

    indicatorSetting = getIndicatorSetting()
    indicators = []
    
    for ind in indicatorSetting:
        indicators.append(ind_dic[ind](data=data, tickerName=ticker, patternTitle=pattern))

    # default
    if len(indicators) == 0:
        indicators.append(ExperimentalIndicator(data=data, tickerName=ticker, patternTitle=pattern))

    return indicators