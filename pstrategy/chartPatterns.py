from ptools import Metrics, WorkPool
from usdata import USMarket
import numpy

def window(center, size) :
    lower = center - min(center, int(size / 2))
    upper = lower + size #upper should be exclusive
    return lower, upper

def arrayWindow(array, center, size) :
    lower, upper = window(center, size)
    return array[lower:upper]

class PriceSignals:
    def __init__(self):
        self.m = Metrics()

    def Type1_buy_point_MACD_bullish_divergence(self, data):
        closePrices = [float(x['Close']) for x in data]
        macd_all = self.m.macd_all(closePrices)
        if macd_all == None:
            return False

        macd_fast = macd_all['fast']
        macd_slow = macd_all['slow']
        macd_histo = macd_all['histo']
        if max(macd_slow[0], macd_fast[0], macd_histo[0]) > 0:
            return False
        if macd_histo[0] < macd_histo[1]:
            return False

        #现在判断是否有"下跌-调整-下跌":
        openPrices = [x['Open'] for x in data]
        sr = self.m.support_and_resistance(openPrices, closePrices, 20)
        sr_price = sr['price']
        lower_bound = min(sr_price[0], sr_price[1]) * 0.95
        upper_bound = max(sr_price[0], sr_price[1]) * 1.05

        if closePrices[0] > lower_bound:
            return False

        idx = 2
        while idx < len(sr_price):
            if sr_price[idx] < lower_bound:
                return False
            if sr_price[idx] > upper_bound:
                break
            idx += 1
        if idx == len(sr_price) or sr_price[idx] < lower_bound:
            return False
        sr_idx = sr['idx']

        #phase1 is the first 'down' phase
        phase1_right_idx = sr_idx[idx-1]
        phase1_left_idx = sr_idx[idx]
        phase1_min_idx = numpy.argmin(closePrices[phase1_right_idx: phase1_left_idx])

        #phase3 is the second (last) 'down' phase
        phase3_right_idx = 0
        phase3_left_idx = sr_idx[0]
        phase3_min_idx = numpy.argmin(closePrices[phase3_right_idx:  phase3_left_idx])

        # price should be new low but macd_fast should not
        if closePrices[phase3_min_idx] > closePrices[phase1_min_idx]:
            return False
        if macd_fast[phase3_min_idx] < macd_fast[phase1_min_idx]:
            return False

        return True


    """
    思想:
        在长期的股价低迷之后,出现了突破,短期均线超过长期均线.但是随后出现调整.
        这个调整伴随着缩量, 可能是shorter trap,可以介入.
        因为交易量数据的不准确, 程序中不读取交易量
    算法:
        下列条件必须首先满足, 否则立即返回False:
            最新价格比上一个价格是下降的;
            短期均线(5)在中期均线(10)和长期均线(20)之下
        # 找到三个区间:
            区间1: 从最近的交易开始,往回找,直到短期均线位于中期和长期均线上方
            区间2: 从区间1的分界日开始往回找,往回找,直到短期均线位于中期和长期均线下方
            区间3: 从区间2的分界日开始,往回找,直到短期均线和中期均线均位于长期均线之上
        # 计算区间2的最高价,区间3的最低价, 以及区间3开始的价格(成为最初价)
            区间3的最低价必须低于最初价20%以上,否则不构成"股价低迷"
            区间2的最高价必须高于区间3最低价的5%,否则不成为突破
            如果当前价低于区间2的最高价15%，则是下跌而不是回调
            如果当前价格是三个区间的最低价，则是下跌而不是回调
        # 如果进行到这里,则可以看成是满足条件
    """
    def Type2_buy_point_pullback_after_breakthrough(self, closePrices):
        ema_short = self.m.ema(closePrices, 5)
        ema_mid   = self.m.ema(closePrices, 10)
        ema_long  = self.m.ema(closePrices, 20)
        if closePrices[0] > closePrices[1]:
            return False
        if ema_short[0] > min(ema_mid[0], ema_long[0]):
            return False
        dsize = len(closePrices)
        pos = []
        idx = 0

        #locate end of section 1
        while idx < dsize and ema_short[idx] < max(ema_mid[idx], ema_long[idx]):
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)

        #locate end of section 2
        while idx < dsize and ema_short[idx] > min(ema_mid[idx], ema_long[idx]):
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)

        #locate end of section 3
        while idx < dsize and (ema_short[idx] < max(ema_mid[idx], ema_long[idx]) or ema_mid[idx] < ema_long[idx]) :
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)

        init_price = closePrices[pos[2]]
        low_section3 = min(closePrices[pos[1]:pos[2]])
        high_section2 = max(closePrices[pos[0]:pos[1]])
        if low_section3 > init_price * 0.8 or high_section2 < low_section3 * 1.05 or \
           closePrices[0] < high_section2 * 0.85:
            return False

        if closePrices[0] < min(closePrices[1:pos[2]]):
            return False

        return True

    #MACD底部背驰
    def MACD_Bottom_reversal2(self, closePrices):
        macd_all = self.m.macd_all(closePrices)
        if macd_all == None:
            return False

        macd_fast = macd_all['fast']
        macd_slow = macd_all['slow']
        macd_histo = macd_all['histo']
        if max(macd_slow[0], macd_fast[0]) > 0:
            return False
        if macd_histo[0] < macd_histo[1]:
            return False

        #find gold crosses
        gold_crosses = []
        required = 2
        for idx in range(len(macd_histo) - 1):
            # if there is a dead cross before the first gold cross, False
            if len(gold_crosses) == 0 and \
                    (macd_histo[idx] < 0 and macd_histo[idx+1] >= 0):
                return False
            if macd_histo[idx] > 0 and macd_histo[idx+1] <= 0:
                curLen = len(gold_crosses)
                if curLen > 0 and idx - gold_crosses[curLen-1] < 7:
                    continue # gold crosses are too close, just noise, ignore
                gold_crosses.append(idx)
                if len(gold_crosses) == required:
                    break
        if len(gold_crosses) < required:
            return False

        # Am I coming late?
        # reversal coming a long time after previous gold cross? yes -> must be weak
        if gold_crosses[0] > 20 or\
           gold_crosses[1] - gold_crosses[0] > 55:
            return False

        fcrossed = [macd_fast[x] for x in gold_crosses]
        assert(len(fcrossed) > 1)
        # if 'gold' cross is made with lower macd values, not good
        if fcrossed[0] < fcrossed[1]:
            return False

        # gprices = [closePrices[x] for x in gold_crosses]
        gprices = [min(arrayWindow(closePrices, x, 14)) for x in gold_crosses]
        assert(len(gprices) > 1)
        # if price is moving higher while gold crosses move higher, no reversal
        if gprices[0] > gprices[1]:
            return False

        return True

    #Note that the 'Open' data of the current day is not reliable, so let's not depend on it
    def Bottom_Up(self, openPrices, closePrices, lows, highs):
        #previous bar must be a nagative bar
        if not (closePrices[1] < openPrices[1]):
            return False
        #current price must be higher than previous close
        if not (closePrices[0] > closePrices[1]):
            return False

        #if any recent close price is higher than ema_5 or ema_10, pass
        #a low price is necessary for profitable reversal
        ema_5  = Metrics().ema(closePrices, 5)
        ema_10 = Metrics().ema(closePrices, 10)
        for idx in range(1, 3):
            if closePrices[idx] > min(ema_5[idx], ema_10[idx]):
                return False

        # look back 300 bars for support and resistence, very old bars are not reliable
        sr = self.m.support_and_resistance(openPrices[:300], closePrices[:300])
        myrange = {'min': lows[1], 'max':max(closePrices[0], highs[1])}
        foundSupport = False
        supportIdx = -1
        for i in range(len(sr['price'])):
            price = sr['price'][i]
            if price > myrange['max']:
                continue
            if price < myrange['min']:
                return False
            idx = sr['idx'][i]
            # 如果之前跌破了找到的这个支撑点，那么这个支撑点已经作废了
            if min(closePrices[2:idx]) < price:
                return False
            foundSupport = True
            supportIdx = idx
            break

        if not foundSupport:
            return False

        prevMax = max(closePrices[1:supportIdx])
        #print(str([supportIdx, prevMax, closePrices[0]]))

        if closePrices[0] > prevMax * 0.9:
            return False

        return True

    def New_High(self, data):
        if len(data) < 100:
            return False
        cutoff = 7
        maxhistory = 80
        closePrices = [x['Close'] for x in data]
        recentMaxClose = max(closePrices[:cutoff])

        previousHigh = max([x['High'] for x in data][cutoff:maxhistory])
        previousLow = min([x['Low'] for x in data][cutoff:maxhistory])

        if previousHigh > recentMaxClose:
            return False

        if previousLow < recentMaxClose * 0.9:
            return False

        ema5 = self.m.ema(closePrices, 5)
        ema10 = self.m.ema(closePrices, 10)
        ema20 = self.m.ema(closePrices, 20)

        if ema5[0] > ema10[0] and ema10[0] > ema20[0]:
            return True

        return False

class ChartPatterns:
    def __init__(self, watchlist, datasets):
        self.market_stopped = False
        self.symbols = watchlist
        self.missing_data = []
        self.missing_analysis = []
        self.metrics = {sym : {} for sym in watchlist}
        self.datasets = datasets

    # Type1_buy_point_MACD_bullish_divergence
    def signal_Type1_buy_point(self, symbols):
        name = '一类买点'
        result = []
        for sym in symbols:
            try:
                if PriceSignals().Type1_buy_point_MACD_bullish_divergence(self.datasets[sym]):
                    result.append(sym)
            except:
                if sym not in self.missing_analysis:
                    self.missing_analysis.append(sym)
        return {'name':name, 'result':result}

    # Type2_buy_point_pullback_after_breakthrough
    def signal_Type2_buy_point(self, symbols):
        name = '二类买点'
        result = []
        for sym in symbols:
            closePrices = [float(x['Close']) for x in self.datasets[sym]]
            try:
                if PriceSignals().Type2_buy_point_pullback_after_breakthrough(closePrices):
                    result.append(sym)
            except:
                if sym not in self.missing_analysis:
                    self.missing_analysis.append(sym)
        return {'name':name, 'result':result}


    def signal_MACD_bottom_reversal(self, symbols):
        name = 'MACD底部背驰'
        result = []
        for sym in symbols:
            volumes = [float(x['Volume']) for x in self.datasets[sym]]
            if max(volumes[:10]) < 500000: #skip whose volume is less than 500K
                continue
            closePrices = [float(x['Close']) for x in self.datasets[sym]]
            try:
                if PriceSignals().MACD_Bottom_reversal2(closePrices):
                    result.append(sym)
            except:
                if sym not in self.missing_analysis:
                    self.missing_analysis.append(sym)
        return {'name':name, 'result':result}

    def singal_bottom_up(self, symbols):
        #插入线，待入线，切入线, 包线
        name = '反弹'
        result = []
        for sym in symbols:
            try:
                openPrices = [x['Open'] for x in self.datasets[sym]]
                closePrices = [x['Close'] for x in self.datasets[sym]]
                lowPrices = [x['Low'] for x in self.datasets[sym]]
                highPrices = [x['High'] for x in self.datasets[sym]]
                if PriceSignals().Bottom_Up(openPrices, closePrices, lowPrices, highPrices):
                    result.append(sym)
            except:
                if sym not in self.missing_analysis:
                    self.missing_analysis.append(sym)
        return {'name':name, 'result':result}

    def signal_new_high(self, symbols):
        name = '新高'
        result = []
        for sym in symbols:
            try:
                if PriceSignals().New_High(self.datasets[sym]):
                    result.append(sym)
            except:
                if sym not in self.missing_analysis:
                    self.missing_analysis.append(sym)
        return {'name':name, 'result':result}

    def run_rule(self, rule, symbols):
        ret = rule(symbols)
        self.wpool.lock()
        self.all_rule_results.append(ret)
        self.wpool.unlock()

    def run(self):
        self.all_rule_results = []

        rules = [
                 self.signal_Type1_buy_point,
                 self.signal_MACD_bottom_reversal,
                 self.signal_new_high,
                 ]
        # self.signal_Type2_buy_point,
        # self.singal_bottom_up

        wpool = WorkPool(10)
        self.wpool = wpool
        for rule in rules:
            wpool.start_work_arg2(self.run_rule, rule, self.symbols)
        wpool.wait_for_all()

        for result in self.all_rule_results:
            print(result['name'] + ': '+ ' '.join(result['result']))

        if len(self.missing_data) > 0:
            print('missing data: ' + ' '.join(self.missing_data))

        if len(self.missing_analysis) > 0:
            print('skipped symbols: ' + ' '.join(self.missing_analysis))


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

