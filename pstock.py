#!/usr/bin/env python

from yahoo_finance import Share
from datetime import datetime, timedelta

def read_watchlist() :
    return [line.strip() for line in open("watchlist.txt", 'r')]

def get_current_prices(symbols) :
    return {sym : Share(sym).get_price() for sym in symbols }

# XXX history from 80 days ago until previous trading day
def get_history(symbols) :
    # XXX today should be today is it's a trading day, or the last trading day
    # XXX prev_trading_day is the further previous trading day
    prev_trading_day = datetime.now() - timedelta(days = 1)
    date_80_days_ago = prev_trading_day - timedelta(days = 80)
    start = date_80_days_ago.date().isoformat()
    end   = prev_trading_day.date().isoformat()

    return {sym : Share(sym).get_historical(start, end) for sym in symbols}

def main() :
    watchlist = read_watchlist()
    print watchlist

    current_prices = get_current_prices(watchlist)
    print current_prices

    history = get_history(watchlist)
    print history

if __name__ == '__main__' :
    main()