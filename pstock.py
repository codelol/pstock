#!/usr/bin/env python3

from yahoo_finance import Share
from googlefinance import getQuotes
from tabulate import tabulate
from datetime import datetime, timedelta
import time, sys, traceback

def read_watchlist() :
    return [line.strip() for line in open("watchlist.txt", 'r')]

def print_red(str):
    print("\033[91m{}\033[0m".format(str))

def get_all_history(symbols) :
    print('requesting history data')
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

    ret = {sym : [{'Close':'0'}] + Share(sym).get_historical(start, end) for sym in symbols}
    print('received history data')
    return ret

class TA:
    def __init__(self, watchlist, full_history):
        self.market_stopped = False
        self.symbols = watchlist
        self.aggregates = {sym : {} for sym in watchlist}
        self.full_history = full_history
        self.interests_sma = [5, 10, 20]
        self.rules = [self.rule_large_negative_followed_by_small_positive,
                      self.rule_breakthrough_sma,
                      self.rule_sma_crossing,
                      self.rule_price_gaps,
                      self.rule_price_range_compare,
                      self.rule_volume_breakout]

    def get_latest(self):
        print('Requesting latest info: ' + datetime.now().isoformat())
        errmsg = ''
        market_stopped = True
        for sym in self.symbols :
            old_price = self.full_history[sym][0]['Close']
            # or Yahoo if Google is not available
            ydata = Share(sym)
            self.full_history[sym][0]['Close'] = ydata.get_price()
            try:
                # use Google API for no-delay quotes if the service is available
                self.full_history[sym][0]['Close'] = getQuotes(sym)[0]['LastTradePrice']
            except:
                errmsg = 'Google API error: ' + str(sys.exc_info()[0])

            if old_price != self.full_history[sym][0]['Close']:
                market_stopped = False
                self.full_history[sym][0]['Open'] = ydata.get_open()
                self.full_history[sym][0]['Low']   = ydata.get_days_low()
                self.full_history[sym][0]['High']  = ydata.get_days_high()
                self.full_history[sym][0]['Volume']  = ydata.get_volume()

        return errmsg, market_stopped

    def cal_simple_moving_average(self) :
        for sym in self.symbols :
            for days in self.interests_sma :
                self.aggregates[sym]['sma'+str(days)] = sum([float(x['Close']) for x in self.full_history[sym][0:days]]) / days
                self.aggregates[sym]['sma'+str(days)+'_prev'] = sum([float(x['Close']) for x in self.full_history[sym][1:days+1]]) / days

    def calculations(self):
        self.cal_simple_moving_average()

    def rule_large_negative_followed_by_small_positive(self, sym):
        cur_open = float(self.full_history[sym][0]['Open'])
        cur_close = float(self.full_history[sym][0]['Close'])
        prev_open = float(self.full_history[sym][1]['Open'])
        prev_close = float(self.full_history[sym][1]['Close'])
        all_sma = [self.aggregates[sym]['sma'+str(x)] for x in self.interests_sma]
        # previous day is negative, and current day is positive
        if (prev_close < prev_open and cur_close > cur_open
            # current price must be at a low level, e.g., sma5 < sma20
            and all_sma[0] < all_sma[2]
            # negative range is at least 1.5 times larger than positive
            and abs(prev_close - prev_open) > 1.5 * abs(cur_close - cur_open)
            # opening price of today is gapped down
            and cur_open < prev_close):
                print(sym+': 插入线，待入线，切入线 -- large negative day followed by small positive day')

    # If stock price has crossed multiple SMA lines
    def rule_breakthrough_sma(self, sym):
        day1 = self.interests_sma[0]
        day2 = self.interests_sma[1]
        day3 = self.interests_sma[2]

        cur_sma1 = self.aggregates[sym]['sma'+str(day1)]
        pre_sma1 = self.aggregates[sym]['sma'+str(day1)+'_prev']

        cur_sma2 = self.aggregates[sym]['sma'+str(day2)]
        pre_sma2 = self.aggregates[sym]['sma'+str(day2)+'_prev']

        cur_sma3 = self.aggregates[sym]['sma'+str(day3)]
        pre_sma3 = self.aggregates[sym]['sma'+str(day3)+'_prev']

        cur_price = float(self.full_history[sym][0]['Close'])
        pre_price = float(self.full_history[sym][1]['Close'])
        if cur_price > max(cur_sma1, cur_sma2, cur_sma3) and pre_price < min(pre_sma1, pre_sma2, pre_sma3):
            print_red(sym+': crossing up all SMA lines from yesterday to today.')
        elif cur_price < min(cur_sma1, cur_sma2, cur_sma3) and pre_price > max(pre_sma1, pre_sma2, pre_sma3):
            print_red(sym+': crossing down all SMA lines from yesterday to today.')

        cur_open = float(self.full_history[sym][0]['Open'])
        if cur_price > max(cur_sma1, cur_sma2, cur_sma3) and cur_open < min(cur_sma1, cur_sma2, cur_sma3):
            print_red(sym+': crossing up all SMA lines from open to now.')
        elif cur_price < min(cur_sma1, cur_sma2, cur_sma3) and cur_open > max(cur_sma1, cur_sma2, cur_sma3):
            print_red(sym+': crossing down all SMA lines from open to now.')

    # If one SMA lines crosses another
    def rule_sma_crossing(self, sym):
        day1 = self.interests_sma[0]
        day2 = self.interests_sma[1]
        day3 = self.interests_sma[2]

        cur_sma1 = self.aggregates[sym]['sma'+str(day1)]
        pre_sma1 = self.aggregates[sym]['sma'+str(day1)+'_prev']

        cur_sma2 = self.aggregates[sym]['sma'+str(day2)]
        pre_sma2 = self.aggregates[sym]['sma'+str(day2)+'_prev']

        cur_sma3 = self.aggregates[sym]['sma'+str(day3)]
        pre_sma3 = self.aggregates[sym]['sma'+str(day3)+'_prev']

        cur_sma1_minus_cur_sma2 = cur_sma1 - cur_sma2
        pre_sma1_minus_pre_sma2 = pre_sma1 - pre_sma2

        msg = ''
        if (cur_sma1_minus_cur_sma2 * pre_sma1_minus_pre_sma2) <= 0:
            if cur_sma1_minus_cur_sma2 > pre_sma1_minus_pre_sma2:
                msg += ' sma'+str(day1) + ' crossing up sma'+str(day2)+'.'
            elif cur_sma1_minus_cur_sma2 < pre_sma1_minus_pre_sma2:
                msg += ' sma'+str(day1) + ' crossing down sma'+str(day2)+'.'
            else:
                msg += ' sma'+str(day1) + ' and sma'+str(day2) + ' are both 0.'

        cur_sma1_minus_cur_sma3 = cur_sma1 - cur_sma3
        pre_sma1_minus_pre_sma3 = pre_sma1 - pre_sma3

        if (cur_sma1_minus_cur_sma3 * pre_sma1_minus_pre_sma3) <= 0:
            if cur_sma1_minus_cur_sma3 > pre_sma1_minus_pre_sma3:
                msg += ' sma'+str(day1) + ' crossing up sma'+str(day3)+'.'
            elif cur_sma1_minus_cur_sma3 < pre_sma1_minus_pre_sma3:
                msg += ' sma'+str(day1) + ' crossing down sma'+str(day3)+'.'
            else:
                msg += ' sma'+str(day1) + ' and sma'+str(day3) + ' are both 0'

        cur_sma2_minus_cur_sma3 = cur_sma2 - cur_sma3
        pre_sma2_minus_pre_sma3 = pre_sma2 - pre_sma3

        if (cur_sma2_minus_cur_sma3 * pre_sma2_minus_pre_sma3) <= 0:
            if cur_sma2_minus_cur_sma3 > pre_sma2_minus_pre_sma3:
                msg += ' sma'+str(day2) + ' crossing up sma'+str(day3)+'.'
            elif cur_sma2_minus_cur_sma3 < pre_sma2_minus_pre_sma3:
                msg += ' sma'+str(day2) + ' crossing down sma'+str(day3)+'.'
            else:
                msg += ' sma'+str(day2) + ' and sma'+str(day3) + ' are both 0.'

        if len(msg) > 0:
            print(sym+':'+msg)

    def rule_price_gaps(self, sym):
        cur_low = float(self.full_history[sym][0]['Low'])
        cur_high = float(self.full_history[sym][0]['High'])
        prev_low = float(self.full_history[sym][1]['Low'])
        prev_high = float(self.full_history[sym][1]['High'])

        if cur_low > prev_high:
            print(sym+': gap up. Gap size: ' + '{0:+.2f}%'.format((cur_low - prev_high)/prev_high * 100) + \
            ' {0:+.2f}$'.format(cur_low - prev_high) + \
            ' ({0:+.2f}'.format(prev_high)+' -> '+ '{0:+.2f})'.format(cur_low))
        if cur_high < prev_low:
            print(sym+': gap down. Gap size: '+ '{0:+.2f}%'.format((cur_high - prev_low)/prev_low * 100) + \
            ' {0:+.2f}$'.format(cur_high - prev_low) + \
            ' ({0:+.2f}'.format(prev_low)+' -> '+ '{0:+.2f})'.format(cur_high))

    def rule_price_range_compare(self, sym):
        cur_low = float(self.full_history[sym][0]['Low'])
        cur_high = float(self.full_history[sym][0]['High'])
        prev_low = float(self.full_history[sym][1]['Low'])
        prev_high = float(self.full_history[sym][1]['High'])

        cur_range_total = abs(cur_low - cur_high)
        prev_range_total = abs(prev_low - prev_high)

        cur_close = float(self.full_history[sym][0]['Close'])
        cur_open = float(self.full_history[sym][0]['Open'])
        prev_close = float(self.full_history[sym][1]['Close'])
        prev_open = float(self.full_history[sym][1]['Open'])

        cur_range_body = abs(cur_close - cur_open)
        prev_range_body = abs(prev_close - prev_open)

        if ((round(cur_range_total, 2) == 0 and round(prev_range_total, 2) == 0) or
            (round(cur_range_body, 2) == 0 and round(prev_range_body, 2) == 0)):
            print('price range is not valid')
            return

        if (cur_range_total > prev_range_total + 0.001 and
            cur_low < prev_low and cur_high > prev_high) :
            print(sym+': cur-day Total price range larger than that of yesterday. ' +
                  '({0:.2f}'.format(prev_low) +', '+ '{0:.2f})'.format(prev_high) + ' -> ' +
                  '({0:.2f}'.format(cur_low) +', '+ '{0:.2f})'.format(cur_high))

        if (cur_range_body > prev_range_body + 0.001 and
            min(cur_open, cur_close) < min(prev_open, prev_close) and
            max(cur_open, cur_close) > max(prev_open, prev_close)) :
            print(sym+': cur-day Body price range larger than that of yesterday' +
                  '({0:.2f}'.format(prev_open) +', '+ '{0:.2f})'.format(prev_close) + ' -> ' +
                  '({0:.2f}'.format(cur_open) +', '+ '{0:.2f})'.format(cur_close))

        if (cur_range_total < prev_range_total - 0.001 and
            cur_low > prev_low and cur_high < prev_high) :
            print(sym+': cur-day Total price range smaller than that of yesterday' +
                  '({0:.2f}'.format(prev_low) +', '+ '{0:.2f})'.format(prev_high) + ' -> ' +
                  '({0:.2f}'.format(cur_low) +','+ '{0:.2f})'.format(cur_high))

        if (cur_range_body < prev_range_body - 0.001 and
            min(cur_open, cur_close) > min(prev_open, prev_close) and
            max(cur_open, cur_close) < max(prev_open, prev_close)) :
            print(sym+': cur-day body price range smaller than that of yesterday' +
                  '({0:.2f}'.format(prev_open) +', '+ '{0:.2f})'.format(prev_close) + ' -> ' +
                  '({0:.2f}'.format(cur_open) +', '+ '{0:.2f})'.format(cur_close))

    def rule_volume_breakout(self, sym):
        # If market is still trading, the current day's High and Low are not updated
        if not self.market_stopped:
            return

        msg = ''
        threshold = 1.15
        day_volume = float(self.full_history[sym][0]['Volume'])
        for days in [5, 10]:
            avgtmp = sum([float(x['Volume']) for x in self.full_history[sym][1:days+1]]) / days
            if day_volume >= avgtmp * threshold :
                msg += ' cur-day volume up prev '+str(days)+'-day average by '+'{0:+.0f}%'.format((day_volume - avgtmp) * 100 / avgtmp)+'.'

        week_volume = sum([float(x['Volume']) for x in self.full_history[sym][0:5]])
        prev4week_volume = (sum([float(x['Volume']) for x in self.full_history[sym][5:20+5]])) / (20 / 5)
        # condition "len(msg) > 0" means: don't print weekly volume breakout unless there is a day volume breakout
        if week_volume >= prev4week_volume * threshold and len(msg) > 0:
                msg += ' cur-week volume up prev 4-week average by '+'{0:+.0f}%'.format((week_volume - prev4week_volume) * 100 / prev4week_volume)+'.'

        if len(msg) > 0:
            print(sym+':'+msg)

    def run_rules(self):
        for sym in self.symbols:
            for rule in self.rules:
                try:
                        rule(sym)
                except Exception as err:
                        print('Skipped one rule for '+sym)
                        traceback.print_tb(err.__traceback__)

    def print_results(self):
        day1 = self.interests_sma[0]
        day2 = self.interests_sma[1]
        day3 = self.interests_sma[2]
        headers = ['Symbol', 'Price', 'Change%', 'Change',
                   'sma('+str(day1)+' - '+str(day2)+')',
                   'sma('+str(day1)+' - '+str(day3)+')',
                   'sma('+str(day2)+' - '+str(day3)+')',
                   ]
        rows = []
        for sym in self.symbols :
            r = []
            price_change = float(self.full_history[sym][0]['Close']) - float(self.full_history[sym][1]['Close'])
            r.append(sym)
            r.append(float(self.full_history[sym][0]['Close']))
            r.append('{0:+.2f}'.format(price_change * 100 / float(self.full_history[sym][1]['Close'])))
            r.append('{0:+.2f}'.format(price_change))
            r.append('{0:+.2f}'.format(float(self.aggregates[sym]['sma'+str(day1)]) - float(self.aggregates[sym]['sma'+str(day2)])))
            r.append('{0:+.2f}'.format(float(self.aggregates[sym]['sma'+str(day1)]) - float(self.aggregates[sym]['sma'+str(day3)])))
            r.append('{0:+.2f}'.format(float(self.aggregates[sym]['sma'+str(day2)]) - float(self.aggregates[sym]['sma'+str(day3)])))
            rows.append(r)
        print(tabulate(rows, headers))

    def loop(self):
        sleep_time = 300
        while True:
            try:
                errmsg, self.market_stopped = self.get_latest()
                if len(errmsg) > 0:
                    print(errmsg)

                self.calculations()
                self.print_results()
                self.run_rules()
                print('============++++++++============')

                if self.market_stopped:
                    print('Market is closed. Quit now.')
                    sleep_time = 0
                    return
            except Exception as err:
                traceback.print_tb(err.__traceback__)
                print('Retrying in '+str(sleep_time)+' seconds...')
            finally:
                time.sleep(sleep_time)

def main() :
    watchlist = read_watchlist()
    print(watchlist)

    # put history info into full_history
    while True:
        try:
            full_history = get_all_history(watchlist)
            break
        except:
            sleep_time = 60
            print('Unable to retrieve history data: ' + sys.exc_info()[0])
            print('Retrying in '+str(sleep_time)+' seconds...')
            time.sleep(sleep_time)

    ta = TA(watchlist, full_history)
    ta.loop()

if __name__ == '__main__' :
    main()
