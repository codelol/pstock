from ptools import Metrics
from usdata import USMarket

class TripleScreen:
    def __init__(self, watchlist, datasetLong, datasetMid = None, datasetShort = None):
        self.watchlist = watchlist
        self.datasetLong = datasetLong
        self.datasetMid = datasetMid
        self.datasetShort = datasetShort

    def long_opportunities(self):
        picked1 = []
        for sym in self.watchlist:
            if self.pulsesystem_should_long(sym, self.datasetLong):
                picked1.append(sym)

        if self.datasetMid == None:
            return picked1

        picked2 = []
        for sym in picked1:
            #if self.macd_buy_point(sym, self.datasetMid):
            if self.forceindex_should_long(sym, self.datasetMid):
                picked2.append(sym)

        return picked2

    def pulsesystem_should_long(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        macd_all = Metrics().macd_all(closePrices)
        if macd_all == None: # not enough data
            return False
        macd_h = macd_all['histo']
        ema_fast = Metrics().ema(closePrices, 10)
        sma_slow = Metrics().sma(closePrices, 26)
        # macd and ema rising, and price is higher than half-year average
        try:
            if closePrices[0] < sma_slow[0]:
                return False
            if macd_h[0] < macd_h[1]:
                return False
            #if ema_fast[0] < max(ema_fast[1:5]):
                #return False
            if sma_slow[0] < max(sma_slow[1:5]):
                return False
            return True
        except:
            pass
        return False

    def macd_buy_point(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        macd_h = Metrics().macd_all(closePrices)['histo']
        ema = Metrics().ema(closePrices, 30)
        # (1) macd-h going up; (2) still negative; (3) price declining but still above ema
        if macd_h[0] >= macd_h[1] and closePrices[0] > max(closePrices[1], ema[0]):
           #price is above ema30
            return True
        return False


    def forceindex_should_long(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        volumes = [float(x['Volume']) for x in data[sym]]
        forceIndex = Metrics().forceIndex(closePrices, volumes)
        if forceIndex[0] < 0:
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
    watchlist = ['ORBC']
    marketData = USMarket(watchlist, '2016-06-19')

    weekly, missing1 = marketData.getData('weekly')
    daily, missing2 = marketData.getData('daily')
    all_missing = set(missing1) | set(missing2)
    if len(all_missing) > 0:
        print('symbols missing data: ' + str(all_missing))

    symlist = [sym for sym in watchlist if sym not in all_missing]
    ts = TripleScreen(symlist, weekly, daily)
    decision = ts.run()
    print(str(decision))


if __name__ == '__main__' :
    main()
