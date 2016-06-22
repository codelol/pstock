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
            if self.screen1_should_long(sym, self.datasetLong):
                picked1.append(sym)

        picked2 = []
        for sym in picked1:
            if self.screen2_should_long(sym, self.datasetLong):
                picked2.append(sym)

        return picked2

    def screen1_should_long(self, sym, data):
        closePrices = [float(x['Close']) for x in data[sym]]
        macd_h = Metrics().macd(closePrices)
        if macd_h[0] > macd_h[1] and macd_h[1] < 0:
            return True
        return False

    def screen2_should_long(self, sym, data):
        # closePrices = [float(x['Close']) for x in data[sym]]
        return True

    def run(self):
        ret = {'long': None, 'short': None}
        ret['long'] = self.long_opportunities()
        return ret


def main() :
    watchlist = ['AAPL', 'JD']
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