from unittest import TestCase

from ptools.metrics import Metrics
from usdata import USMarket

class TestMetrics(TestCase):
    def test_ema(self):
        datapoints = list(reversed([22.27, 22.19, 22.08, 22.17, 22.18, 22.13, 22.23, 22.43, 22.24,
                      22.29, 22.15, 22.39]))
        result = Metrics().ema(datapoints, 10)
        assert(len(result) == 3)
        assert(result[0] > 22.241 and result[0] < 22.242)
        print(str(result))

    def test_forceIndex(self):
        prices = list(reversed([14.33, 14.23, 13.98, 13.96, 13.93, 13.84, 13.99, 14.31, 14.51, 14.46, 14.61, 14.48, 14.53, 14.56]))
        vol = list(reversed([0, 45579, 66285, 51761, 69341, 41631, 73499, 55427, 61082, 33325, 39191, 51128, 46505, 44562]))
        fi1 = Metrics().forceIndex(prices, vol, 1)
        assert(len(fi1) == len(prices) - 1)
        assert(fi1[0] > 1336 and fi1[0] < 1337)
        print(str(fi1))

    def test_rsi(self):
        data = list(reversed([44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28,
                46.28, 46.00, 46.03]))
        result = (Metrics().rsi(data))
        assert(len(result) == len(data) - 14)
        assert(result[0] > 66.480 and result[0] < 66.490)
        assert(result[1] > 66.240 and result[1] < 66.250)
        assert(result[2] > 70.460 and result[2] < 70.470)

    def test_support_and_resistance(self):
        sym = 'UCO'
        data, missing = USMarket([sym], '2016-08-11').getData()
        sdata = data[sym][:50]
        openPrices = [e['Open'] for e in sdata]
        closePrices = [e['Close'] for e in sdata]
        sr = Metrics().support_and_resistance(openPrices, closePrices)
        print(str(sr))