#!/usr/bin/env python

from yahoo_finance import Share
from googlefinance import getQuotes
from tabulate import tabulate
from datetime import datetime, timedelta
import time
import sys

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
        self.rules = [self.rule_sma_crossing]

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
        self.merge_current_and_history_close_prices()
        self.cal_simple_moving_average()

    def rule_sma_crossing(self):
        for sym in self.symbols:
            day1 = self.interests_sma[0]
            day2 = self.interests_sma[1]
            day3 = self.interests_sma[2]

            cur_sma1 = self.latest_data[sym]['sma'+str(day1)]
            pre_sma1 = self.latest_data[sym]['sma'+str(day1)+'_prev']

            cur_sma2 = self.latest_data[sym]['sma'+str(day2)]
            pre_sma2 = self.latest_data[sym]['sma'+str(day2)+'_prev']

            cur_sma3 = self.latest_data[sym]['sma'+str(day3)]
            pre_sma3 = self.latest_data[sym]['sma'+str(day3)+'_prev']

            cur_sma1_minus_cur_sma2 = cur_sma1 - cur_sma2
            pre_sma1_minus_pre_sma2 = pre_sma1 - pre_sma2

            if (cur_sma1_minus_cur_sma2 * pre_sma1_minus_pre_sma2) <= 0:
                if cur_sma1_minus_cur_sma2 > pre_sma1_minus_pre_sma2:
                    print sym+': sma'+str(day1) + ' crossing up sma'+str(day2)
                elif cur_sma1_minus_cur_sma2 < pre_sma1_minus_pre_sma2:
                    print sym+': sma'+str(day1) + ' crossing down sma'+str(day2)
                else:
                    print sym+': sma'+str(day1) + ' and sma'+str(day2) + ' are both 0'

            cur_sma1_minus_cur_sma3 = cur_sma1 - cur_sma3
            pre_sma1_minus_pre_sma3 = pre_sma1 - pre_sma3

            if (cur_sma1_minus_cur_sma3 * pre_sma1_minus_pre_sma3) <= 0:
                if cur_sma1_minus_cur_sma3 > pre_sma1_minus_pre_sma3:
                    print sym+': sma'+str(day1) + ' crossing up sma'+str(day3)
                elif cur_sma1_minus_cur_sma3 < pre_sma1_minus_pre_sma3:
                    print sym+': sma'+str(day1) + ' crossing down sma'+str(day3)
                else:
                    print sym+': sma'+str(day1) + ' and sma'+str(day3) + ' are both 0'

            cur_sma2_minus_cur_sma3 = cur_sma2 - cur_sma3
            pre_sma2_minus_pre_sma3 = pre_sma2 - pre_sma3

            if (cur_sma2_minus_cur_sma3 * pre_sma2_minus_pre_sma3) <= 0:
                if cur_sma2_minus_cur_sma3 > pre_sma2_minus_pre_sma3:
                    print sym+': sma'+str(day2) + ' crossing up sma'+str(day3)
                elif cur_sma2_minus_cur_sma3 < pre_sma2_minus_pre_sma3:
                    print sym+': sma'+str(day2) + ' crossing down sma'+str(day3)
                else:
                    print sym+': sma'+str(day2) + ' and sma'+str(day3) + ' are both 0'

    def run_rules(self):
        for rule in self.rules:
            rule()

    def print_results(self):
        day1 = self.interests_sma[0]
        day2 = self.interests_sma[1]
        day3 = self.interests_sma[2]
        headers = ['Symbol', 'Price', 'Change', 'Change%',
                   'sma('+str(day1)+' - '+str(day2)+')',
                   'sma('+str(day1)+' - '+str(day3)+')',
                   'sma('+str(day2)+' - '+str(day3)+')',
                   ]
        rows = []
        for sym in self.symbols :
            r = []
            price_change = float(self.latest_data[sym]['price']) - float(self.full_history[sym]['close_prices'][0])
            r.append(sym)
            r.append(self.latest_data[sym]['price'])
            r.append('{0:+.2f}'.format(price_change))
            r.append('{0:+.2f}'.format(price_change * 100 / float(self.full_history[sym]['close_prices'][0])))
            r.append('{0:+.2f}'.format(float(self.latest_data[sym]['sma'+str(day1)]) - float(self.latest_data[sym]['sma'+str(day2)])))
            r.append('{0:+.2f}'.format(float(self.latest_data[sym]['sma'+str(day1)]) - float(self.latest_data[sym]['sma'+str(day3)])))
            r.append('{0:+.2f}'.format(float(self.latest_data[sym]['sma'+str(day2)]) - float(self.latest_data[sym]['sma'+str(day3)])))
            rows.append(r)
        print tabulate(rows, headers)

    def loop(self):
        sleep_time = 60
        while True:
            try:
                self.get_current_prices()
                self.calculations()
                self.print_results()
                self.run_rules()
                print '============++++++++============'
            except:
                print 'Unexpected error happened:', sys.exc_info()[0]
                print 'Retrying in '+str(sleep_time)+' seconds...'
            finally:
                time.sleep(sleep_time)

def main() :
    watchlist = read_watchlist()
    print watchlist

    # put history info into full_history
    while True:
        try:
            full_history = get_all_history(watchlist)
            break
        except:
            sleep_time = 60
            print 'Unable to retrieve history data: ', sys.exc_info()[0]
            print 'Retrying in '+str(sleep_time)+' seconds...'
            time.sleep(sleep_time)

    ta = TA(watchlist, full_history)
    ta.loop()

if __name__ == '__main__' :
    main()
