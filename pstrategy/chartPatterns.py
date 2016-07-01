from ptools import Metrics, Signals
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
        picked = []
        s = Signals()
        for sym in self.symbols:
            try:
                closePrices = [float(x['Close']) for x in self.datasets[sym]]
                if s.MACD_bullish_divergence(closePrices) :
                    picked.append(sym)
            except:
                self.symbols.remove(sym)
                self.missing_analysis.append(sym)
        if len(picked) > 0:
            return {'name': 'MACD_bullish_divergence', 'value': picked}
        return None

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

    # 在长期的股价低迷之后,出现了突破,短期均线超过长期均线.但是随后出现调整.
    # 这个调整伴随着缩量, 可能是shorter trap,可以介入.
    # 因为交易量数据的不准确, 程序中不读取交易量
    def pullback_after_breakthrough(self):
        picked = []
        for sym in self.symbols:
            closePrices = [float(x['Close']) for x in self.datasets[sym]]
            # not pullback if price is increasing
            if closePrices[0] > closePrices[1]:
                continue
            emaArray0 = self.metrics[sym]['ema' + str(self.interests_ema[0])]
            emaArray1 = self.metrics[sym]['ema' + str(self.interests_ema[1])]
            emaArray2 = self.metrics[sym]['ema' + str(self.interests_ema[2])]
            # price dropped below 'long'-term ema, too much to be a pullback
            if closePrices[0] < emaArray2[0]:
                continue
            emaGaps = [(a - b) for a, b in zip(emaArray0, emaArray1)]
            # short-term ema is still above long-term, no pull-back yet.
            if emaGaps[0] > 0:
                continue
            history = []
            i = 0

            while i < len(emaGaps):
                if emaGaps[i] > 0:
                    break
                i += 1
            if i == len(emaGaps):
                continue
            history.append(i)

            while i < len(emaGaps):
                if emaGaps[i] < 0:
                    break
                i += 1
            if i == len(emaGaps):
                continue
            history.append(i - sum(history))

            while i < len(emaGaps):
                if emaGaps[i] > 0:
                    break
                i += 1
            if i == len(emaGaps):
                continue
            history.append(i - sum(history))

            #history[2]: initially the days when ema_0 < ema_1
            #history[1]: then the days when ema_0 > ema_1
            #history[1]: now pullback --the days when ema_0 > ema_1
            assert(len(history) == 3)
            if history[2] < 10 or  history[2] < history[1] * 1.5: #initial phase is too short, non-solid base
                continue
            picked.append(sym)
        if len(picked) > 0:
            return {'name': '突破后的回调(检查是否缩量)', 'value': picked}
        return None

    def run(self):
        all_results = []

        result = self.run_signals()
        if result != None:
            all_results.append(result)

        rules = [self.large_negative_followed_by_small_positive,
                 self.pullback_after_breakthrough]

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
    watchlist = ['AAPL', 'GPRO', 'PANW']
    print(watchlist)
    marketData = USMarket(watchlist)

    data, missing = marketData.getData('daily')
    ta = ChartPatterns(watchlist, data)
    ta.run()
    print('missing? '+str(missing))

if __name__ == '__main__' :
    main()

