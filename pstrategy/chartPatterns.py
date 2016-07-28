from ptools import Metrics, PriceSignals, WorkPool
from usdata import USMarket

class ChartPatterns:
    def __init__(self, watchlist, datasets):
        self.market_stopped = False
        self.symbols = watchlist
        self.missing_data = []
        self.missing_analysis = []
        self.metrics = {sym : {} for sym in watchlist}
        self.datasets = datasets
        self.interests_ema = [7, 14, 30]
        self.cal_exponential_moving_average()

    def cal_exponential_moving_average(self) :
        for sym in self.symbols :
            try:
                datapoints = [float(x['Close']) for x in self.datasets[sym]]
                for days in self.interests_ema :
                    self.metrics[sym]['ema'+str(days)] = Metrics().ema(datapoints, days)
            except:
                self.symbols.remove(sym)
                self.missing_data.append(sym)

    # Type1_buy_point_MACD_bullish_divergence
    def signal_Type1_buy_point(self, sym):
        name = '一类买点'
        closePrices = [float(x['Close']) for x in self.datasets[sym]]
        try:
            if PriceSignals().Type1_buy_point_MACD_bullish_divergence(closePrices):
                self.wpool.lock()
                if name not in self.all_rule_results.keys():
                    self.all_rule_results[name] = [sym]
                else:
                    self.all_rule_results[name].append(sym)
                self.wpool.unlock()
        except:
            if sym not in self.missing_analysis:
                self.missing_analysis.append(sym)

    # Type2_buy_point_pullback_after_breakthrough
    def signal_Type2_buy_point(self, sym):
        name = '二类买点'
        closePrices = [float(x['Close']) for x in self.datasets[sym]]
        try:
            if PriceSignals().Type2_buy_point_pullback_after_breakthrough(closePrices):
                self.wpool.lock()
                if name not in self.all_rule_results.keys():
                    self.all_rule_results[name] = [sym]
                else:
                    self.all_rule_results[name].append(sym)
                self.wpool.unlock()
        except:
            if sym not in self.missing_analysis:
                self.missing_analysis.append(sym)

    def large_negative_followed_by_small_positive(self, sym):
        name = '插入线，待入线，切入线'
        try:
            openPrices = [float(x['Open']) for x in self.datasets[sym]]
            closePrices = [float(x['Close']) for x in self.datasets[sym]]
            #if current session is negative, pass
            if closePrices[0] < openPrices[0]:
                return
            #if previous session is positive, pass
            if closePrices[1] > openPrices[1]:
                return
            #if previous session didn't drop at least 1%, pass
            if (openPrices[1] - closePrices[1]) < openPrices[1] * 0.01:
                return
            #if current session opened higher than last session's range, pass
            if openPrices[0] >= min(openPrices[1], closePrices[1]):
                return

            #if any recent close price is than ema_5 or ema_10, pass
            #a low price is necessary for profitable reversal
            ema_5  = Metrics().ema(closePrices, 5)
            ema_10 = Metrics().ema(closePrices, 10)
            shouldSkip = False
            for idx in range(1, 3):
                if closePrices[idx] > min(ema_5[idx], ema_10[idx]):
                    shouldSkip = True
                    break
            if shouldSkip:
                return

            self.wpool.lock()
            if name not in self.all_rule_results.keys():
                self.all_rule_results[name] = [sym]
            else:
                self.all_rule_results[name].append(sym)
            self.wpool.unlock()
        except:
            if sym not in self.missing_analysis:
                self.missing_analysis.append(sym)

    def run_rules_for_sym(self, sym):
        rules = [self.signal_Type1_buy_point,
                 self.signal_Type2_buy_point,
                 self.large_negative_followed_by_small_positive]
        for rule in rules:
            rule(sym)

    def run(self):
        self.all_rule_results = {}

        wpool = WorkPool(10)
        self.wpool = wpool
        for sym in self.symbols:
            wpool.start_work(self.run_rules_for_sym, sym)
        wpool.wait_for_all()

        rulenames = ['一类买点', '二类买点', '插入线，待入线，切入线']
        rules_with_results = [r for r in rulenames if r in self.all_rule_results.keys()]
        for name in rules_with_results:
            symbolStr = ' '.join(self.all_rule_results[name])
            print(name + ': '+ symbolStr)

        if len(self.missing_data) > 0:
            print('missing data: ' + str(self.missing_data))

        if len(self.missing_analysis) > 0:
            print('skipped symbols: ' + str(self.missing_analysis))


def main() :
    watchlist = ['AAPL', 'GPRO', 'PANW', 'TWTR']
    print(watchlist)
    marketData = USMarket(watchlist, '2016-06-10')

    data, missing = marketData.getData('daily')
    ta = ChartPatterns(watchlist, data)
    ta.run()
    print('missing? '+str(missing))

if __name__ == '__main__' :
    main()

