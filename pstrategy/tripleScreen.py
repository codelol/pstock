from ptools import Metrics
from usdata import USMarket

class TripleScreen:
    def __init__(self, watchlist, datasetLong, datasetMid, datasetShort = None):
        self.watchlist = watchlist
        self.datasetLong = datasetLong
        self.datasetMid = datasetMid
        self.datasetShort = datasetShort

    def long_opportunities(self):
        picked1 = []
        for sym in self.watchlist:
            if self.pulsesystem_should_long(sym, self.datasetLong):
                picked1.append(sym)

        picked2 = []
        for sym in picked1:
            if self.macd_buy_point(sym, self.datasetMid):
                picked2.append(sym)

        return picked2

    def pulsesystem_should_long(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        macd_h = Metrics().macd(closePrices)
        if macd_h == None: # not enough data
            return False
        ema = Metrics().ema(closePrices, 10)
        # macd rising and ema10 rising
        if macd_h[0] >= macd_h[1] and macd_h[0] < 0 and ema[0] >= ema[1]:
            return True
        return False

    def macd_buy_point(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        macd_h = Metrics().macd(closePrices)
        ema = Metrics().ema(closePrices, 30)
        # (1) macd-h going up; (2) still negative; (3) price declining but still above ema
        if macd_h[0] >= macd_h[1] and macd_h[1] < 0 and closePrices[1] > closePrices[0] > ema[0]:
           #price is above ema30
            return True
        return False


    def forceindex_should_long(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        volumes = [float(x['Volume']) for x in data[sym]]
        forceIndex = Metrics().forceIndex(closePrices, volumes)
        if forceIndex[0] > forceIndex[1] and forceIndex[1] < 0:
            return True
        return False

    def rsi_should_long(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        rsiArray = Metrics().rsi(closePrices)
        for i in range(10):
            if rsiArray[i] > rsiArray[i+1] and rsiArray[i+1] < 40:
                return True
        return False

    def run(self):
        ret = {'long': None, 'short': None}
        ret['long'] = self.long_opportunities()
        return ret


def main() :
    watchlist = ['SQ']
    print(watchlist)
    marketData = USMarket(watchlist)

    daily, missing1 = marketData.getData('daily')
    weekly, missing2 = marketData.getData('weekly')
    all_missing = set(missing1) | set(missing2)
    if len(all_missing) > 0:
        print('symbols missing data: ' + str(all_missing))

    symlist = [sym for sym in watchlist if sym not in all_missing]
    ts = TripleScreen(symlist, weekly, daily)
    decision = ts.run()
    print(str(decision))


if __name__ == '__main__' :
    main()
