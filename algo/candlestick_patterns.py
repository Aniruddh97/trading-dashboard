import talib
import numpy as np
import streamlit as st

from itertools import compress


def getCandlePatternList(all=False):
    if not all:
        return ['CDLEVENINGDOJISTAR', 'CDLEVENINGSTAR', 'CDLMORNINGDOJISTAR', 'CDLMORNINGSTAR']
    return talib.get_function_groups()['Pattern Recognition']


def getCandlestickPatterns(df, candleIndex):

    if (candleIndex - 15) < df.index.start or candleIndex > (df.index.stop - 1):
        return ['NO_PATTERN']

    df = df[candleIndex-15:candleIndex+1].copy(deep=True)
    df = df.reset_index(drop=True)
    
    op = df['OPEN'].astype(float)
    lo = df['LOW'].astype(float)
    hi = df['HIGH'].astype(float)
    cl = df['CLOSE'].astype(float)

    candlePatterns = talib.get_function_groups()['Pattern Recognition']
    for candle in candlePatterns:
        df[candle] = getattr(talib, candle)(op, hi, lo, cl)

    row = df.iloc[-1]
    patterns = list(compress(row[candlePatterns].keys(), row[candlePatterns].values != 0))
    container = []
    for pattern in patterns:
        if row[pattern] > 0:
            container.append(pattern + '_Bull')
        else:
            container.append(pattern + '_Bear')

    return container


def getLatestCandlePattern(df, all=False):
    
    df = df.tail(15).copy(deep=True)
    df = df.reset_index(drop=True)
    df = getBestCandlestickPattern(df, all)
    pattern = df['candlestick_pattern'][df.index.stop-1]
    rank = candle_rankings[pattern]
    
    return pattern, rank


def getBestCandlestickPattern(df, all=False):
    """
    Recognizes candlestick patterns and appends 2 additional columns to df;
    1st - Best Performance candlestick pattern matched by www.thepatternsite.com
    2nd - # of matched patterns
    """

    op = df['OPEN'].astype(float)
    lo = df['LOW'].astype(float)
    hi = df['HIGH'].astype(float)
    cl = df['CLOSE'].astype(float)

    candlePatterns = getCandlePatternList(all)

    # patterns not found in the patternsite.com
    exclude_items = ('CDLCOUNTERATTACK',
                     'CDLLONGLINE',
                     'CDLSHORTLINE',
                     'CDLSTALLEDPATTERN',
                     'CDLKICKINGBYLENGTH')

    candlePatterns = [candle for candle in candlePatterns if candle not in exclude_items]


    # create columns for each candle
    for candle in candlePatterns:
        df[candle] = getattr(talib, candle)(op, hi, lo, cl)


    df['candlestick_rank'] = np.nan
    df['candlestick_pattern'] = np.nan
    df['candlestick_match_count'] = np.nan
    for index, row in df.iterrows():

        # no pattern found
        if len(row[candlePatterns]) - sum(row[candlePatterns] == 0) == 0:
            df.loc[index, 'candlestick_pattern'] = "NO_PATTERN"
            df.loc[index, 'candlestick_match_count'] = 0
            df.loc[index, 'candlestick_rank'] = np.nan
        # single pattern found
        elif len(row[candlePatterns]) - sum(row[candlePatterns] == 0) == 1:
            # bull pattern 100 or 200
            if any(row[candlePatterns].values > 0):
                pattern = list(compress(row[candlePatterns].keys(), row[candlePatterns].values != 0))[0] + '_Bull'
                df.loc[index, 'candlestick_pattern'] = pattern
                df.loc[index, 'candlestick_match_count'] = 1
                df.loc[index, 'candlestick_rank'] = candle_rankings[pattern]
            # bear pattern -100 or -200
            else:
                pattern = list(compress(row[candlePatterns].keys(), row[candlePatterns].values != 0))[0] + '_Bear'
                df.loc[index, 'candlestick_pattern'] = pattern
                df.loc[index, 'candlestick_match_count'] = 1
                df.loc[index, 'candlestick_rank'] = candle_rankings[pattern]
        # multiple patterns matched -- select best performance
        else:
            # filter out pattern names from bool list of values
            patterns = list(compress(row[candlePatterns].keys(), row[candlePatterns].values != 0))
            container = []
            for pattern in patterns:
                if row[pattern] > 0:
                    container.append(pattern + '_Bull')
                else:
                    container.append(pattern + '_Bear')
            rank_list = [candle_rankings[p] for p in container]
            if len(rank_list) == len(container):
                rank_index_best = rank_list.index(min(rank_list))
                df.loc[index, 'candlestick_pattern'] = container[rank_index_best]
                df.loc[index, 'candlestick_match_count'] = len(container)
                df.loc[index, 'candlestick_rank'] = candle_rankings[container[rank_index_best]]
    # clean up candle columns
    cols_to_drop = candlePatterns
    df.drop(cols_to_drop, axis = 1, inplace = True)

    return df

candle_rankings = {
        "NO_PATTERN": 999,
        "CDLMATCHINGLOW_Bull": 0.5,
        "CDLHARAMI_Bull": 0.6,
        "CDLHOMINGPIGEON_Bull": 0.7,
        "CDLRICKSHAWMAN_Bull": 0.71,
        "CDLBELTHOLD_Bull": 0.72,
        "CDLCLOSINGMARUBOZU_Bull": 0.73,
        "CDL3INSIDE_Bull": 0.74,
        "CDL3OUTSIDE_Bull": 0.75,
        "CDLLONGLEGGEDDOJI_Bull": 0.76,
        "CDLDRAGONFLYDOJI_Bull": 0.8,
        "CDL3LINESTRIKE_Bull": 1,
        "CDL3LINESTRIKE_Bear": 2,
        "CDL3BLACKCROWS_Bear": 3,
        "CDLEVENINGSTAR_Bear": 4,
        "CDLTASUKIGAP_Bull": 5,
        "CDLTASUKIGAP_Bear": 5,
        "CDLINVERTEDHAMMER_Bull": 6,
        "CDLABANDONEDBABY_Bull": 8,
        "CDLBREAKAWAY_Bull": 10,
        "CDLBREAKAWAY_Bear": 10,
        "CDLMORNINGSTAR_Bull": 12,
        "CDLPIERCING_Bull": 13,
        "CDLSTICKSANDWICH_Bull": 14,
        "CDLTHRUSTING_Bear": 15,
        "CDLINNECK_Bear": 17,
        "CDL3INSIDE_Bear": 56,
        "CDLDARKCLOUDCOVER_Bear": 22,
        "CDLIDENTICAL3CROWS_Bear": 24,
        "CDLMORNINGDOJISTAR_Bull": 25,
        "CDLXSIDEGAP3METHODS_Bull": 27,
        "CDLXSIDEGAP3METHODS_Bear": 26,
        "CDLTRISTAR_Bull": 28,
        "CDLTRISTAR_Bear": 76,
        "CDLGAPSIDESIDEWHITE_Bull": 46,
        "CDLGAPSIDESIDEWHITE_Bear": 29,
        "CDLEVENINGDOJISTAR_Bear": 30,
        "CDL3WHITESOLDIERS_Bull": 32,
        "CDLONNECK_Bear": 33,
        "CDL3OUTSIDE_Bear": 39,
        "CDLSEPARATINGLINES_Bull": 36,
        "CDLSEPARATINGLINES_Bear": 40,
        "CDLHARAMI_Bear": 72,
        "CDLLADDERBOTTOM_Bull": 41,
        "CDLCLOSINGMARUBOZU_Bear": 43,
        "CDLTAKURI_Bull": 47,
        "CDLDOJISTAR_Bull": 49,
        "CDLDOJISTAR_Bear": 51,
        "CDLHARAMICROSS_Bull": 50,
        "CDLHARAMICROSS_Bear": 80,
        "CDLADVANCEBLOCK_Bear": 54,
        "CDLSHOOTINGSTAR_Bear": 55,
        "CDLMARUBOZU_Bull": 71,
        "CDLMARUBOZU_Bear": 57,
        "CDLUNIQUE3RIVER_Bull": 60,
        "CDL2CROWS_Bear": 61,
        "CDLBELTHOLD_Bear": 63,
        "CDLHAMMER_Bull": 65,
        "CDLHIGHWAVE_Bull": 67,
        "CDLHIGHWAVE_Bear": 67,
        "CDLSPINNINGTOP_Bull": 69,
        "CDLSPINNINGTOP_Bear": 73,
        "CDLUPSIDEGAP2CROWS_Bear": 74,
        "CDLGRAVESTONEDOJI_Bull": 77,
        "CDLHIKKAKEMOD_Bull": 82,
        "CDLHIKKAKEMOD_Bear": 81,
        "CDLHIKKAKE_Bull": 85,
        "CDLHIKKAKE_Bear": 83,
        "CDLENGULFING_Bull": 84,
        "CDLENGULFING_Bear": 91,
        "CDLMATHOLD_Bull": 86,
        "CDLHANGINGMAN_Bear": 87,
        "CDLRISEFALL3METHODS_Bull": 94,
        "CDLRISEFALL3METHODS_Bear": 89,
        "CDL3STARSINSOUTH_Bull": 103,
        "CDLDOJI_Bull": 104,
    }