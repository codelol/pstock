#!/usr/bin/env python

from yahoo_finance import Share
from datetime import datetime, timedelta

def read_watchlist() :
    return [line.strip() for line in open("watchlist.txt", 'r')]

def get_current_prices(symbols) :
    return {sym : Share(sym).get_price() for sym in symbols }

def get_all_history(symbols) :
    def get_latest_trading_day() :
        # return today if it is a trading day, otherwise return the most recent one
        today = datetime.today()
        return {
            6 : today - timedelta(days = 2), # Sunday, return Friday
            5 : today - timedelta(days = 1), # Saturday, return Friday
                                             # Monday to Friday is [0, 4]
        }.get(today.weekday(), today)

    latest_trading_day = get_latest_trading_day()
    print 'Lastest trading day:',latest_trading_day.date().isoformat()

    history_starting_day = latest_trading_day - timedelta(days = 40)
    history_ending_day = latest_trading_day - timedelta(days = 1)
    start = history_starting_day.date().isoformat()
    end   = history_ending_day.date().isoformat()

    return {sym : Share(sym).get_historical(start, end) for sym in symbols}

def get_history_close_prices(full_history):
    history_close_prices = {}
    for sym in full_history.keys() :
        history_close_prices[sym] = [x['Close'] for x in full_history[sym]]
    return history_close_prices

def cal_simple_moving_average(prices, days) :
    sma = {}
    for sym in prices.keys() :
        sma[sym] = sum([float(x) for x in prices[sym][0:days]]) / days
    return sma

def merge_current_and_history_close_prices(symbols, current_prices, history_close_prices) :
    merged_prices = {}
    for sym in symbols :
        merged_prices[sym] = [current_prices[sym]] + history_close_prices[sym]
    return merged_prices

def print_results(symbols, current_prices, history_close_prices, sma5, sma10, sma20) :
    for sym in symbols :
        price_change = float(current_prices[sym]) - float(history_close_prices[sym][0])
        print sym,
        print current_prices[sym],
        print str(price_change),
        print '{0:.2%}'.format(price_change / float(history_close_prices[sym][0])),
        print str(float(sma5[sym]) - float(sma10[sym])),
        print str(float(sma5[sym]) - float(sma20[sym]))


def main() :
    watchlist = read_watchlist()
    print watchlist

    current_prices = get_current_prices(watchlist)
    # print current_prices

    full_history = get_all_history(watchlist)
    # print full_history

    history_close_prices = get_history_close_prices(full_history)
    # print history_close_prices

    merged_prices = merge_current_and_history_close_prices(watchlist, current_prices, history_close_prices)
    # print merged_prices

    sma5 = cal_simple_moving_average(merged_prices, 5)
    # print sma5

    sma10 = cal_simple_moving_average(merged_prices, 10)
    # print sma10

    sma20 = cal_simple_moving_average(merged_prices, 20)
    # print sma20

    print_results(watchlist, current_prices, history_close_prices, sma5, sma10, sma20)

if __name__ == '__main__' :
    main()