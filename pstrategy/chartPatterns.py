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

    # Type1_buy_point_MACD_bullish_divergence
    def signal_Type1_buy_point(self, sym):
        name = '一类买点'
        try:
            if PriceSignals().Type1_buy_point_MACD_bullish_divergence(self.datasets[sym]):
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


    def signal_MACD_bottom_reversal(self, sym):
        name = 'MACD底部背驰'
        closePrices = [float(x['Close']) for x in self.datasets[sym]]
        try:
            if PriceSignals().MACD_Bottom_reversal(closePrices):
                self.wpool.lock()
                if name not in self.all_rule_results.keys():
                    self.all_rule_results[name] = [sym]
                else:
                    self.all_rule_results[name].append(sym)
                self.wpool.unlock()
        except:
            if sym not in self.missing_analysis:
                self.missing_analysis.append(sym)

    def singal_bottom_up(self, sym):
        #插入线，待入线，切入线, 包线
        name = '反弹'
        try:
            openPrices = [x['Open'] for x in self.datasets[sym]]
            closePrices = [x['Close'] for x in self.datasets[sym]]
            lowPrices = [x['Low'] for x in self.datasets[sym]]
            highPrices = [x['High'] for x in self.datasets[sym]]
            if PriceSignals().Bottom_Up(openPrices, closePrices, lowPrices, highPrices):
                self.wpool.lock()
                if name not in self.all_rule_results.keys():
                    self.all_rule_results[name] = [sym]
                else:
                    self.all_rule_results[name].append(sym)
                self.wpool.unlock()
        except:
            if sym not in self.missing_analysis:
                self.missing_analysis.append(sym)

    def signal_new_high(self, sym):
        name = '新高'
        try:
            if PriceSignals().New_High(self.datasets[sym]):
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
                 self.signal_MACD_bottom_reversal,
                 self.signal_new_high,
                 self.singal_bottom_up]
        for rule in rules:
            rule(sym)

    def run(self):
        self.all_rule_results = {}

        wpool = WorkPool(10)
        self.wpool = wpool
        for sym in self.symbols:
            wpool.start_work(self.run_rules_for_sym, sym)
        wpool.wait_for_all()

        # rulenames = ['一类买点', '二类买点', '反弹', '新高']
        rulenames = ['一类买点', 'MACD底部背驰', '新高', '反弹']
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

