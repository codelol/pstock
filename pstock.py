#!/usr/bin/env python

from yahoo_finance import Share
from googlefinance import getQuotes
from tabulate import tabulate
from datetime import datetime, timedelta

def read_watchlist() :
    return [line.strip() for line in open("watchlist.txt", 'r')]

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


class TA:
    def __init__(self, watchlist, full_history):
        self.symbols = watchlist
        self.latest_data = {sym : {} for sym in watchlist}
        self.full_history = full_history
        self.interests_sma = [5, 10, 20]

    def get_current_prices(self):
        print 'Requesting current prices:', datetime.now().isoformat()
        for sym in self.symbols :
            # use Google API for no-delay quotes
            self.latest_data[sym]['price'] = getQuotes(sym)[0]['LastTradePrice']

    def merge_current_and_history_close_prices(self) :
        merged_prices = {}
        for sym in self.symbols :
            merged_prices[sym] = [self.latest_data[sym]['price']] + self.full_history[sym]['close_prices']
        self.merged_prices = merged_prices

    def cal_simple_moving_average(self) :
        for sym in self.symbols :
            for days in self.interests_sma :
                self.latest_data[sym]['sma'+str(days)] = sum([float(x) for x in self.merged_prices[sym][0:days]]) / days
                self.latest_data[sym]['sma'+str(days)+'_prev'] = sum([float(x) for x in self.merged_prices[sym][1:days+1]]) / days

    def calculations(self):
        self.get_current_prices()
        self.merge_current_and_history_close_prices()
        self.cal_simple_moving_average()

    def print_results(self):
        headers = ['Symbol', 'Price', 'Change', 'Change%', 'sma(5 - 10)', 'sma(5 - sma20)']
        rows = []
        for sym in self.symbols :
            r = []
            price_change = float(self.latest_data[sym]['price']) - float(self.full_history[sym]['close_prices'][0])
            r.append(sym)
            r.append(self.latest_data[sym]['price'])
            r.append('{0:+.2f}'.format(price_change))
            r.append('{0:+.2f}'.format(price_change * 100 / float(self.full_history[sym]['close_prices'][0])))
            r.append('{0:+.2f}'.format(float(self.latest_data[sym]['sma5']) - float(self.latest_data[sym]['sma10'])))
            r.append('{0:+.2f}'.format(float(self.latest_data[sym]['sma5']) - float(self.latest_data[sym]['sma20'])))
            rows.append(r)
        print tabulate(rows, headers)

    def loop(self):
        import time
        while True:
            self.calculations()
            self.print_results()
            print '============++++++++============'
            time.sleep(60)

def main() :
    watchlist = read_watchlist()
    print watchlist

    # put history info into full_history
    full_history = get_all_history(watchlist)

    ta = TA(watchlist, full_history)
    ta.loop()

if __name__ == '__main__' :
    main()
