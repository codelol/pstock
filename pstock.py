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

    history_starting_day = latest_trading_day - timedelta(days = 20)
    history_ending_day = latest_trading_day - timedelta(days = 1)
    start = history_starting_day.date().isoformat()
    end   = history_ending_day.date().isoformat()

    return {sym : Share(sym).get_historical(start, end) for sym in symbols}

def get_history_close_prices(full_history):
    history_close_prices = {}
    for sym in full_history.keys() :
        info = full_history[sym]
        prices = []
        for each_day in info:
            prices.append(each_day['Close'])
        history_close_prices[sym] = prices
    return history_close_prices

def main() :
    watchlist = read_watchlist()
    print watchlist

    current_prices = get_current_prices(watchlist)
    print current_prices

    full_history = get_all_history(watchlist)
    print full_history

    history_close_prices = get_history_close_prices(full_history)
    print history_close_prices

if __name__ == '__main__' :
    main()