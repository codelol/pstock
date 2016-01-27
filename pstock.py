#!/usr/bin/env python

from yahoo_finance import Share

def read_watchlist() :
    return [line.strip() for line in open("watchlist.txt", 'r')]

def get_current_prices(watchlist) :
    return {symbol : Share(symbol).get_price() for symbol in watchlist }

def main() :
    watchlist = read_watchlist()
    print watchlist
    current_prices = get_current_prices(watchlist)
    print current_prices

if __name__ == '__main__' :
    main()