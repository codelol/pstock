from ptools import Metrics, PriceSignals
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

    def run_signals(self):
        resultsArray = []
        type1Picked = []
        type2Picked = []
        s = PriceSignals()
        for sym in self.symbols:
            try:
                closePrices = [float(x['Close']) for x in self.datasets[sym]]
                if s.Type1_buy_point_MACD_bullish_divergence(closePrices):
                    type1Picked.append(sym)

                if s.Type2_buy_point_pullback_after_breakthrough(closePrices):
                    type2Picked.append(sym)
            except:
                self.symbols.remove(sym)
                self.missing_analysis.append(sym)
        if len(type1Picked) > 0:
            resultsArray.append({'name':'一类买点', 'value':type1Picked})
        if len(type2Picked) > 0:
            resultsArray.append({'name':'二类买点', 'value':type2Picked})
        return resultsArray

    def large_negative_followed_by_small_positive(self):
        picked = []
        for sym in self.symbols:
            try:
                cur_open = float(self.datasets[sym][0]['Open'])
                cur_close = float(self.datasets[sym][0]['Close'])
                prev_open = float(self.datasets[sym][1]['Open'])
                prev_close = float(self.datasets[sym][1]['Close'])
                all_ema = [self.metrics[sym]['ema'+str(x)][0] for x in self.interests_ema]
                # previous day is negative, and current day is positive
                if (prev_close < prev_open and cur_close > cur_open
                    # current price must be at a low level, e.g., ema5 < ema20
                    and all_ema[0] < all_ema[2]
                    # negative range is at least 1.5 times larger than positive
                    and abs(prev_close - prev_open) > 1.5 * abs(cur_close - cur_open)
                    # opening price of today is gapped down
                    and cur_open < prev_close):
                        picked.append(sym)
            except:
                self.symbols.remove(sym)
                self.missing_analysis.append(sym)
        if len(picked) > 0:
            return {'name': '插入线，待入线，切入线', 'value': picked}
        return None

    def run(self):
        all_results = []

        result_array = self.run_signals()
        for result in result_array:
            all_results.append(result)

        rules = [self.large_negative_followed_by_small_positive]
        for rule in rules:
            result = rule()
            if result != None:
                all_results.append(result)

        for result in all_results:
            symbolStr = ' '.join(result['value'])
            print(result['name'] + ': '+ symbolStr)

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

