"""
Package for metrics calculations
closePrices[0] is the most recent price
"""

from usdata import USMarket

class Metrics:
    # exponential moving average
    def ema(self, datapoints, days) :
        if days == 1:
            return datapoints
        ratio = float(2 / (days + 1))
        cur_ema = 0
        emas = []
        for i in reversed(range(len(datapoints))):
            cur_ema = datapoints[i] * ratio + cur_ema * (1 - ratio)
            emas.insert(0, cur_ema)
        return emas

    # Calculate a 12-day EMA of closing prices.
    # Calculate a 26-day EMA of closing prices.
    # Subtract the 26-day EMA from the 12-day EMA, and plot their difference as a solid line. This is the fast MACD line.
    # Calculate a 9-day EMA of the fast line, and plot the result as a dashed line. This is the slow Signal line.
    def macd(self, datapoints, d1 = 12, d2 = 26, d3 = 9):
        ema_d1 = self.ema(datapoints, d1)
        ema_d2 = self.ema(datapoints, d2)
        macdline = [(x - y) for x, y in zip(ema_d1, ema_d2)]
        signalLine = self.ema(macdline, d3)
        histogram = [(x - y) for x, y in zip(macdline, signalLine)]
        return histogram

    def forceIndex(self, closePrices, volumes, d = 13):
        assert(len(closePrices) == len(volumes))
        index1 = []
        for i in range(len(closePrices) - 1):
            index1.append((closePrices[i] - closePrices[i+1] * volumes[i]))
        return self.ema(index1, d)

def main():
    sym = 'AAPL'
    watchlist = [sym]
    print(watchlist)
    marketData = USMarket(watchlist)
    priceHistory, missing = marketData.getData('daily')
    closePrices = [float(x['Close']) for x in priceHistory[sym]]
    volumes = [float(x['Volume']) for x in priceHistory[sym]]

    mts = Metrics()
    # macd_histo = mts.macd(closePrices)
    # print(str(macd_histo))

    forceIndex = mts.forceIndex(closePrices, volumes)
    print(str(forceIndex))

if __name__ == '__main__' :
    main()