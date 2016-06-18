from tabulate import tabulate
import traceback
from ptools import Metrics
from usdata import USMarket

def is_cross(prices):
    open_price = float(prices['Open'])
    close_price = float(prices['Close'])

    if abs(open_price - close_price) < close_price * 0.001:
        return True
    return False

def is_positive(prices):
    return float(prices['Close']) > float(prices['Open'])

def is_negative(prices):
    return float(prices['Close']) < float(prices['Open'])

class ChartPatterns:
    def __init__(self, watchlist, datasets, verbose = False, weekly_mode = False):
        self.market_stopped = False
        self.symbols = watchlist
        self.missing_data = []
        self.verbose = verbose
        self.weekly_mode = weekly_mode
        self.tu = 'week' if weekly_mode else 'day'
        self.aggregates = {sym : {} for sym in watchlist}
        self.metrics = {sym : {} for sym in watchlist}
        self.datasets = datasets
        self.stashed_daily_history = datasets
        self.interests_ema = [5, 10, 20]
        self.buy_signals = ''
        self.sell_signals = ''
        self.other_signals = ''
        self.rules = [self.rule_double_needle_bottom,
                      self.rule_large_negative_followed_by_emall_positive,
                      self.rule_long_side_canon,
                      self.rule_short_side_canon,
                      self.rule_morning_star,
                      self.rule_death_star,
                      self.rule_breakthrough_ema,
                      self.rule_ema_crossing,
                      self.rule_price_new_high,
                      self.rule_price_gaps,
                      self.rule_price_range_compare]

    def convert_into_weekly_prices(self):
        self.stashed_daily_history = self.datasets
        tmp_history = {}
        for sym in self.symbols :
            tmp_history[sym] = []

            try:
                # analyze 20 weeks (100 trading days) at most
                for i in range(20):
                    price_dict = {}
                    price_dict['Open'] = self.datasets[sym][i * 5 + 4]['Open']
                    price_dict['Close'] = self.datasets[sym][i * 5]['Close']
                    price_dict['High'] = str(max([float(x['High']) for x in self.datasets[sym][(i*5):(i*5+5)]]))
                    price_dict['Low'] = str(min([float(x['Low']) for x in self.datasets[sym][(i*5):(i*5+5)]]))
                    price_dict['Volume'] = str(min([float(x['Volume']) for x in self.datasets[sym][(i*5):(i*5+5)]]))
                    tmp_history[sym] = tmp_history[sym] + [price_dict]
            except:
                # missing data for this symbol
                self.symbols.remove(sym)
                self.missing_data.append(sym)

        # now self.datasets should be a weekly prices
        self.datasets = tmp_history
        print('Converted daily prices into weekly prices')

    def cal_simple_moving_average(self) :
        for sym in self.symbols :
            try:
                for days in self.interests_ema :
                    self.aggregates[sym]['ema'+str(days)] = sum([float(x['Close']) for x in self.datasets[sym][0:days]]) / days
                    self.aggregates[sym]['ema'+str(days)+'_prev'] = sum([float(x['Close']) for x in self.datasets[sym][1:days+1]]) / days
            except:
                self.symbols.remove(sym)
                self.missing_data.append(sym)

    def cal_exponential_moving_average(self) :
        for sym in self.symbols :
            try:
                datapoints = [float(x['Close']) for x in self.datasets[sym]]
                for days in self.interests_ema :
                    self.metrics[sym]['ema'] = Metrics().ema(datapoints, days)
                    self.aggregates[sym]['ema'+str(days)] = self.metrics[sym]['ema'][0]
                    self.aggregates[sym]['ema'+str(days)+'_prev'] = self.metrics[sym]['ema'][1]
            except:
                self.symbols.remove(sym)
                self.missing_data.append(sym)

    def get_all_emas(self, sym):
        day1 = self.interests_ema[0]
        day2 = self.interests_ema[1]
        day3 = self.interests_ema[2]
        cur_ema1 = float(self.aggregates[sym]['ema'+str(day1)])
        cur_ema2 = float(self.aggregates[sym]['ema'+str(day2)])
        cur_ema3 = float(self.aggregates[sym]['ema'+str(day3)])
        return [cur_ema1, cur_ema2, cur_ema3]

    def calculations(self):
        self.cal_exponential_moving_average()

    def rule_double_needle_bottom(self, sym):
        cur_close = float(self.datasets[sym][0]['Close'])
        cur_ema1 = self.aggregates[sym]['ema'+str(self.interests_ema[0])]
        cur_ema2 = self.aggregates[sym]['ema'+str(self.interests_ema[1])]
        cur_ema3 = self.aggregates[sym]['ema'+str(self.interests_ema[2])]

        # if price is not at a low level, don't bother
        if cur_close > min(cur_ema1, cur_ema2, cur_ema3):
            return

        cur_open = float(self.datasets[sym][0]['Open'])
        cur_low  = float(self.datasets[sym][0]['Low'])
        body_size = abs(cur_open - cur_close)
        lower_needle_size = min(cur_open, cur_close) - cur_low

        # if the lower_needle_size is not large enough, don't bother
        if lower_needle_size < body_size * 2:
            return

        # now let's look for if we have double bottoms recently
        days_to_check = 10
        for i in range(1, days_to_check):
            tmp_low = float(self.datasets[sym][i]['Low'])
            if (cur_low - tmp_low) > cur_close * 0.002:
                # there was a lower bottom previously, so today is not bottom
                return

        for i in range(1, days_to_check):
            tmp_low = float(self.datasets[sym][i]['Low'])
            if abs(tmp_low - cur_low) < cur_close * 0.002:
                self.buy_signals += '\n' + sym + ': double needle bottom'
                return

    def rule_large_negative_followed_by_emall_positive(self, sym):
        cur_open = float(self.datasets[sym][0]['Open'])
        cur_close = float(self.datasets[sym][0]['Close'])
        prev_open = float(self.datasets[sym][1]['Open'])
        prev_close = float(self.datasets[sym][1]['Close'])
        all_ema = [self.aggregates[sym]['ema'+str(x)] for x in self.interests_ema]
        # previous day is negative, and current day is positive
        if (prev_close < prev_open and cur_close > cur_open
            # current price must be at a low level, e.g., ema5 < ema20
            and all_ema[0] < all_ema[2]
            # negative range is at least 1.5 times larger than positive
            and abs(prev_close - prev_open) > 1.5 * abs(cur_close - cur_open)
            # opening price of today is gapped down
            and cur_open < prev_close):
                self.buy_signals += '\n' + sym + ': 插入线，待入线，切入线'

    #3-day pattern: positive, negative, positive. This is a possible buy signal
    def rule_long_side_canon(self, sym):
        if (is_positive(self.datasets[sym][2]) and
            is_negative(self.datasets[sym][1]) and
            is_positive(self.datasets[sym][0])):
            #the first positive day should be a recent 'new high'
            if (float(self.datasets[sym][2]['Close']) >
                max(float(self.datasets[sym][3]['Close']), float(self.datasets[sym][3]['Open']),
                    float(self.datasets[sym][4]['Close']), float(self.datasets[sym][4]['Open']),
                    float(self.datasets[sym][5]['Close']), float(self.datasets[sym][5]['Open']),
                    float(self.datasets[sym][6]['Close']), float(self.datasets[sym][6]['Open'])
                    )):
                self.buy_signals += '\n' + sym + ': 多方炮/两阳夹一阴'

    #3-day pattern: negative, positive, negative. This is a possible sell signal
    def rule_short_side_canon(self, sym):
        if (is_negative(self.datasets[sym][2]) and
            is_positive(self.datasets[sym][1]) and
            is_negative(self.datasets[sym][0])):
            #the first negative day should be a recent 'new low'
            if (float(self.datasets[sym][2]['Close']) <
                min(float(self.datasets[sym][3]['Close']), float(self.datasets[sym][3]['Open']),
                    float(self.datasets[sym][4]['Close']), float(self.datasets[sym][4]['Open']),
                    float(self.datasets[sym][5]['Close']), float(self.datasets[sym][5]['Open']),
                    float(self.datasets[sym][6]['Close']), float(self.datasets[sym][6]['Open'])
                    )):
                self.sell_signals += '\n' + sym + ': 空方炮/两阴夹一阳'

    def rule_morning_star(self, sym):
        if (is_positive(self.datasets[sym][0]) and
            is_cross(self.datasets[sym][1]) and
            is_negative(self.datasets[sym][2])):

            cur_price = float(self.datasets[sym][0]['Close'])
            if (cur_price < min(self.get_all_emas(sym))):
                self.buy_signals += '\n' + sym + ': Morning Star'

    def rule_death_star(self, sym):
        if (is_negative(self.datasets[sym][0]) and
            is_cross(self.datasets[sym][1]) and
            is_positive(self.datasets[sym][2])):

            cur_price = float(self.datasets[sym][0]['Close'])
            if (cur_price > max(self.get_all_emas(sym))):
                self.sell_signals += '\n' + sym + ': Death/Evening Star'


    # If stock price has crossed multiple ema lines
    def rule_breakthrough_ema(self, sym):
        cur_price = float(self.datasets[sym][0]['Close'])

        day1 = self.interests_ema[0]
        day2 = self.interests_ema[1]
        day3 = self.interests_ema[2]

        cur_ema1 = self.aggregates[sym]['ema'+str(day1)]
        pre_ema1 = self.aggregates[sym]['ema'+str(day1)+'_prev']

        cur_ema2 = self.aggregates[sym]['ema'+str(day2)]
        pre_ema2 = self.aggregates[sym]['ema'+str(day2)+'_prev']

        cur_ema3 = self.aggregates[sym]['ema'+str(day3)]
        pre_ema3 = self.aggregates[sym]['ema'+str(day3)+'_prev']

        cur_open = float(self.datasets[sym][0]['Open'])
        if cur_price > max(cur_ema1, cur_ema2, cur_ema3) and cur_open < min(cur_ema1, cur_ema2, cur_ema3):
            self.buy_signals += '\n'+sym+': crossing up all ema lines from open to now.'
            return
        elif cur_price < min(cur_ema1, cur_ema2, cur_ema3) and cur_open > max(cur_ema1, cur_ema2, cur_ema3):
            self.sell_signals += '\n'+sym+': crossing down all ema lines from open to now.'
            return

        cur_price = float(self.datasets[sym][0]['Close'])
        pre_price = float(self.datasets[sym][1]['Close'])
        if cur_price > max(cur_ema1, cur_ema2, cur_ema3) and pre_price < min(pre_ema1, pre_ema2, pre_ema3):
            self.buy_signals += '\n'+sym+': crossing up all ema lines from previous to current.'
        elif cur_price < min(cur_ema1, cur_ema2, cur_ema3) and pre_price > max(pre_ema1, pre_ema2, pre_ema3):
            self.sell_signals += '\n'+sym+': crossing down all ema lines from previous to current.'

    # If one ema lines crosses another
    def rule_ema_crossing(self, sym):
        day1 = self.interests_ema[0]
        day2 = self.interests_ema[1]
        day3 = self.interests_ema[2]

        cur_ema1 = self.aggregates[sym]['ema'+str(day1)]
        pre_ema1 = self.aggregates[sym]['ema'+str(day1)+'_prev']

        cur_ema2 = self.aggregates[sym]['ema'+str(day2)]
        pre_ema2 = self.aggregates[sym]['ema'+str(day2)+'_prev']

        cur_ema3 = self.aggregates[sym]['ema'+str(day3)]
        pre_ema3 = self.aggregates[sym]['ema'+str(day3)+'_prev']

        cur_ema1_minus_cur_ema2 = cur_ema1 - cur_ema2
        pre_ema1_minus_pre_ema2 = pre_ema1 - pre_ema2

        if (cur_ema1_minus_cur_ema2 * pre_ema1_minus_pre_ema2) <= 0:
            if cur_ema1_minus_cur_ema2 > pre_ema1_minus_pre_ema2:
                self.buy_signals += '\n' + sym + ': ema'+str(day1) + ' crossing up ema'+str(day2)+'.'
            elif cur_ema1_minus_cur_ema2 < pre_ema1_minus_pre_ema2:
                self.sell_signals += '\n' + sym + ': ema'+str(day1) + ' crossing down ema'+str(day2)+'.'
            else:
                pass

        cur_ema2_minus_cur_ema3 = cur_ema2 - cur_ema3
        pre_ema2_minus_pre_ema3 = pre_ema2 - pre_ema3

        if (cur_ema2_minus_cur_ema3 * pre_ema2_minus_pre_ema3) <= 0:
            if cur_ema2_minus_cur_ema3 > pre_ema2_minus_pre_ema3:
                self.buy_signals += '\n' + sym + ': ema'+str(day2) + ' crossing up ema'+str(day3)+'.'
            elif cur_ema2_minus_cur_ema3 < pre_ema2_minus_pre_ema3:
                self.sell_signals += '\n' + sym + ': ema'+str(day2) + ' crossing down ema'+str(day3)+'.'
            else:
                pass

    def rule_price_new_high(self, sym):
        # in weekly_mode, detect 10-week new high; if in daily mode, 20-day new high
        new_high_threshold = 10 if self.weekly_mode else 20
        cur_price = float(self.datasets[sym][0]['Close'])
        day_idx = 1
        while day_idx < len(self.datasets[sym]):
            if cur_price < float(self.datasets[sym][day_idx]['High']):
                break
            day_idx += 1
        if day_idx < new_high_threshold:
            return
        self.buy_signals += '\n' + sym+': '+str(day_idx + 1)+'-'+self.tu+' new high!'

    def rule_price_gaps(self, sym):
        cur_low = float(self.datasets[sym][0]['Low'])
        cur_high = float(self.datasets[sym][0]['High'])
        prev_low = float(self.datasets[sym][1]['Low'])
        prev_high = float(self.datasets[sym][1]['High'])

        if cur_low > prev_high:
            self.buy_signals += '\n'+sym+': gap up. Gap size: ' + \
                                '{0:+.2f}%'.format((cur_low - prev_high)/prev_high * 100) + \
                                ' {0:+.2f}$'.format(cur_low - prev_high) + \
                                ' ({0:+.2f}'.format(prev_high)+' -> '+ '{0:+.2f})'.format(cur_low)
        if cur_high < prev_low:
            self.sell_signals += '\n'+sym+': gap down. Gap size: '+ \
                                 '{0:+.2f}%'.format((cur_high - prev_low)/prev_low * 100) + \
                                 ' {0:+.2f}$'.format(cur_high - prev_low) + \
                                 ' ({0:+.2f}'.format(prev_low)+' -> '+ '{0:+.2f})'.format(cur_high)

    def rule_price_range_compare(self, sym):
        cur_low = float(self.datasets[sym][0]['Low'])
        cur_high = float(self.datasets[sym][0]['High'])
        prev_low = float(self.datasets[sym][1]['Low'])
        prev_high = float(self.datasets[sym][1]['High'])

        cur_range_total = abs(cur_low - cur_high)
        prev_range_total = abs(prev_low - prev_high)

        pattern_found = False
        if (cur_range_total > prev_range_total + 0.001 and
            cur_low < prev_low and cur_high > prev_high) :
            pattern_found = True

        if (cur_range_total < prev_range_total - 0.001 and
            cur_low > prev_low and cur_high < prev_high) :
            pattern_found = True

        if not pattern_found:
            return

        if cur_low < min(self.get_all_emas(sym)):
            self.buy_signals += '\n' + sym + ': price range fluctuation alert. Buy.'

        if cur_high > max(self.get_all_emas(sym)):
            self.sell_signals += '\n' + sym + ': price range fluctuation alert. Sell.'

    def run_rules(self):
        skipped = False
        for sym in self.symbols:
            for rule in self.rules:
                try:
                    rule(sym)
                except Exception as err:
                    if self.verbose:
                        print('Skipped one rule for '+sym)
                        traceback.print_tb(err.__traceback__)
                    else:
                        skipped = True
        if skipped:
            print('-- Some rules are skipped. Turn on verbose to see details. --')

    def print_results(self):
        day1 = self.interests_ema[0]
        day2 = self.interests_ema[1]
        day3 = self.interests_ema[2]
        headers = ['Symbol', 'Price', 'Change%', 'Change',
                   'ema('+str(day1)+' - '+str(day2)+')',
                   'ema('+str(day2)+' - '+str(day3)+')',
                   ]
        rows = []
        for sym in self.symbols :
            try:
                r = []
                price_change = float(self.datasets[sym][0]['Close']) - float(self.datasets[sym][1]['Close'])
                r.append(sym)
                r.append(float(self.datasets[sym][0]['Close']))
                r.append('{0:+.2f}'.format(price_change * 100 / float(self.datasets[sym][1]['Close'])))
                r.append('{0:+.2f}'.format(price_change))
                r.append('{0:+.2f}'.format(float(self.aggregates[sym]['ema'+str(day1)]) - float(self.aggregates[sym]['ema'+str(day2)])))
                r.append('{0:+.2f}'.format(float(self.aggregates[sym]['ema'+str(day2)]) - float(self.aggregates[sym]['ema'+str(day3)])))
                rows.append(r)
            except:
                self.symbols.remove(sym)
                self.missing_data.append(sym)

        print(tabulate(rows, headers))

    def run(self):
        if self.weekly_mode:
            self.convert_into_weekly_prices()

        self.calculations()
        self.print_results()

        self.buy_signals =   '============ Buy Signals ============'
        self.sell_signals =  '=========== Sell Signals ============'
        self.other_signals = '========== Other Signals ============'
        self.run_rules()
        print(self.buy_signals)
        print(self.sell_signals)
        print(self.other_signals)

def main() :
    watchlist = ['AAPL', 'GOOGL']
    print(watchlist)
    marketData = USMarket(watchlist, 'daily')

    ta = ChartPatterns(watchlist, marketData.getData(), False, False)
    ta.run()

if __name__ == '__main__' :
    main()