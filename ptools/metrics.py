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
        init_smas = self.sma(datapoints[(dsize - days) : ], days)
        if init_smas == None or len(init_smas) == 0:
            return None
        assert(len(init_smas) == 1)
        prev_ema = float(init_smas[0])
        emas = [prev_ema]
        for i in reversed(range(dsize - days)):
            cur_ema = (float(datapoints[i]) - float(prev_ema)) * ratio + prev_ema
            emas.insert(0, cur_ema)
            prev_ema = float(cur_ema)
        return emas

    # simple moving average
    def sma(self, datapoints, days):
        if days == 1:
            return datapoints
        dsize = len(datapoints)
        if dsize < days:
            return None
        smas = []
        for i in range(dsize - (days - 1)):
            tmp = float(sum(datapoints[i:i+days]) / float(days))
            smas.append(tmp)
        return smas

    # Calculate a 12-day EMA of closing prices.
    # Calculate a 26-day EMA of closing prices.
    # Subtract the 26-day EMA from the 12-day EMA, and plot their difference as a solid line. This is the fast MACD line.
    # Calculate a 9-day EMA of the fast line, and plot the result as a dashed line. This is the slow Signal line.
    def macd_all(self, datapoints, d1 = 12, d2 = 26, d3 = 9):
        ema_d1 = self.ema(datapoints, d1)
        ema_d2 = self.ema(datapoints, d2)
        if ema_d1 == None or ema_d2 == None:
            return None
        #macd line is also called the fast line
        #signal line is also called the slow line
        macdline = [(x - y) for x, y in zip(ema_d1, ema_d2)]
        signalLine = self.ema(macdline, d3)
        if signalLine == None:
            return None
        histogram = [(x - y) for x, y in zip(macdline, signalLine)]
        return {'fast': macdline, 'slow': signalLine, 'histo': histogram}

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

    def support_and_resistance(self, openPrices, closePrices, window = 10):
        ret = []
        pos = []
        assert(len(openPrices) == len(closePrices))
        datalen = len(openPrices)
        if datalen < window:
            return ret
        for i in range(datalen - window):
            openMax = max(openPrices[i:i+window])
            openMin = min(openPrices[i:i+window])
            closeMax = max(closePrices[i:i+window])
            closeMin = min(closePrices[i:i+window])
            dmax = max(openMax, openMin, closeMax, closeMin)
            dmin = min(openMax, openMin, closeMax, closeMin)
            idx = i + int(window / 2)
            medianmax = max(openPrices[idx], closePrices[idx])
            medianmin = min(openPrices[idx], closePrices[idx])
            if medianmax == dmax:
                ret.append(medianmax)
                pos.append(idx)
            elif medianmin == dmin:
                ret.append(medianmin)
                pos.append(idx)

        print(str(pos))
        return ret
