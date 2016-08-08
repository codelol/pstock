"""
Package for metrics calculations
closePrices[0] is the most recent price
"""

class Metrics:
    # exponential moving average
    def ema(self, datapoints, days) :
        if days == 1:
            return datapoints
        dsize = len(datapoints)
        if dsize < days:
            return None
        ratio = float(2 / (days + 1))
        prev_ema = float(sum(datapoints[dsize - days:dsize]) / days)
        emas = [prev_ema]
        for i in reversed(range(dsize - days)):
            prev_ema = datapoints[i] * ratio + prev_ema * (1 - ratio)
            emas.insert(0, prev_ema)
        return emas

    # simple moving average
    def sma(self, datapoints, days):
        if days == 1:
            return datapoints
        dsize = len(datapoints)
        if dsize < days:
            return None
        smas = []
        for i in range(dsize - days):
            tmp = float(sum(datapoints[i:i+days]) / days)
            smas.append(tmp)
        return smas

    # Calculate a 12-day EMA of closing prices.
    # Calculate a 26-day EMA of closing prices.
    # Subtract the 26-day EMA from the 12-day EMA, and plot their difference as a solid line. This is the fast MACD line.
    # Calculate a 9-day EMA of the fast line, and plot the result as a dashed line. This is the slow Signal line.
    def macd(self, datapoints, d1 = 12, d2 = 26, d3 = 9):
        ema_d1 = self.ema(datapoints, d1)
        ema_d2 = self.ema(datapoints, d2)
        if ema_d1 == None or ema_d2 == None:
            return None
        macdline = [(x - y) for x, y in zip(ema_d1, ema_d2)]
        signalLine = self.ema(macdline, d3)
        if signalLine == None:
            return None
        histogram = [(x - y) for x, y in zip(macdline, signalLine)]
        return histogram

    def forceIndex(self, closePrices, volumes, d = 13):
        assert(len(closePrices) == len(volumes))
        index1 = []
        for i in range(len(closePrices) - 1):
            index1.append((closePrices[i] - closePrices[i+1]) * volumes[i])
        fi = self.ema(index1, d)
        return fi

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
