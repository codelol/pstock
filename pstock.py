#!/usr/bin/env python

from yahoo_finance import Share
from googlefinance import getQuotes
from tabulate import tabulate
from datetime import datetime, timedelta

def read_watchlist() :
    return [line.strip() for line in open("watchlist.txt", 'r')]

def get_current_prices(latest_data, symbols) :
    print 'Requesting latest:', datetime.now().isoformat()
    for sym in symbols :
        # use Google API for no-delay quotes
        latest_data[sym]['price'] = getQuotes(sym)[0]['LastTradePrice']

def get_all_history(symbols) :
    print 'requesting history data'
    def get_latest_trading_day() :
        # return today if it is a trading day, otherwise return the most recent one
        today = datetime.today()
        return {
            6 : today - timedelta(days = 2), # Sunday, return Friday
            5 : today - timedelta(days = 1), # Saturday, return Friday
                                             # Monday to Friday is [0, 4]
        }.get(today.weekday(), today)

    latest_trading_day = get_latest_trading_day()

    history_starting_day = latest_trading_day - timedelta(days = 40)
    history_ending_day = latest_trading_day - timedelta(days = 1)
    start = history_starting_day.date().isoformat()
    end   = history_ending_day.date().isoformat()

    full_history = {sym : Share(sym).get_historical(start, end) for sym in symbols}
    ret = {sym : {} for sym in symbols}

    def get_history_close_prices(full_history):
        history_close_prices = {}
        for sym in full_history.keys() :
            history_close_prices[sym] = [x['Close'] for x in full_history[sym]]
        return history_close_prices

    history_close_prices = get_history_close_prices(full_history)
    for sym in symbols :
        ret[sym]['close_prices'] = history_close_prices[sym]

    print 'received history data'
    return ret

def cal_simple_moving_average(latest_data, prices, days) :
    for sym in prices.keys() :
        latest_data[sym]['sma'+str(days)] = sum([float(x) for x in prices[sym][0:days]]) / days
        latest_data[sym]['sma'+str(days)+'_prev'] = sum([float(x) for x in prices[sym][1:days+1]]) / days

def merge_current_and_history_close_prices(symbols, latest_data, full_history) :
    merged_prices = {}
    for sym in symbols :
        merged_prices[sym] = [latest_data[sym]['price']] + full_history[sym]['close_prices']
    return merged_prices


def print_results(symbols, latest_data, full_history) :
    headers = ['Symbol', 'Price', 'Change', 'Change%', 'sma(5 - 10)', 'sma(5 - sma20)']
    rows = []
    for sym in symbols :
        r = []
        price_change = float(latest_data[sym]['price']) - float(full_history[sym]['close_prices'][0])
        r.append(sym)
        r.append(latest_data[sym]['price'])
        r.append('{0:+.2f}'.format(price_change))
        r.append('{0:+.2f}'.format(price_change * 100 / float(full_history[sym]['close_prices'][0])))
        r.append('{0:+.2f}'.format(float(latest_data[sym]['sma5']) - float(latest_data[sym]['sma10'])))
        r.append('{0:+.2f}'.format(float(latest_data[sym]['sma5']) - float(latest_data[sym]['sma20'])))
        rows.append(r)
    print tabulate(rows, headers)


def analysis(watchlist, full_history, latest_data) :
    # put latest info into latest_data
    get_current_prices(latest_data, watchlist)

    merged_prices = merge_current_and_history_close_prices(watchlist, latest_data, full_history)

    cal_simple_moving_average(latest_data, merged_prices, 5)
    cal_simple_moving_average(latest_data, merged_prices, 10)
    cal_simple_moving_average(latest_data, merged_prices, 20)

    print_results(watchlist, latest_data, full_history)

def main() :
    watchlist = read_watchlist()
    latest_data = {sym : {} for sym in watchlist}
    print watchlist

    # put history info into full_history
    full_history = get_all_history(watchlist)

    analysis(watchlist, full_history, latest_data)

if __name__ == '__main__' :
    main()
