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

    def rsi(self, datapoints, d = 14):
        dsize = len(datapoints)
        if (dsize < d + 1):
            return None
        rsize = dsize - 1
        gains = []
        losses = []
        for i in range(rsize):
            if datapoints[i] > datapoints[i+1]:
                gains.append(datapoints[i] - datapoints[i+1])
                losses.append(0)
            elif datapoints[i] < datapoints[i+1]:
                losses.append(datapoints[i+1] - datapoints[i])
                gains.append(0)
            else:
                gains.append(0)
                losses.append(0)
        avggains = [sum(gains[rsize - d : rsize]) / d]
        avglosses = [sum(losses[rsize - d : rsize]) / d]
        for i in reversed(range(rsize - d)):
            avggains.insert(0, (avggains[0] * 13 + gains[i]) / 14)
            avglosses.insert(0, (avglosses[0] * 13 + losses[i]) /14)

        RSarray = []
        RSI =[]
        for i in range(dsize - d):
            rs = avggains[i] / avglosses[i]
            RSarray.append(rs)
            RSI.append(100 - 100 / (1 + rs))
        return RSI


def testRSI():
    data = list(reversed([44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28,
            46.28, 46.00, 46.03]))
    result = (Metrics().rsi(data))
    assert(len(result) == len(data) - 14)
    assert(result[0] > 66.480 and result[0] < 66.490)
    assert(result[1] > 66.240 and result[1] < 66.250)
    assert(result[2] > 70.460 and result[2] < 70.470)
    print('testRSI passed:' + str(result))

def main():
    sym = 'GOOGL'
    watchlist = [sym]
    print(watchlist)
    marketData = USMarket(watchlist)
    priceHistory, missing = marketData.getData('daily')
    closePrices = [float(x['Close']) for x in priceHistory[sym]]

    mts = Metrics()
    rsi = mts.rsi(closePrices)
    print(str(rsi))

if __name__ == '__main__' :
    main()
    # testRSI()