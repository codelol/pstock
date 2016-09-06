from unittest import TestCase
from usdata import USMarket
from ptools import PriceSignals

class TestPriceSignals(TestCase):
    def test_Bottom_Up(self):
        sym = 'UCO'
        date = '2016-08-03'
        data, missing = USMarket([sym], date).getData()
        sdata = data[sym]
        openPrices = [e['Open'] for e in sdata]
        closePrices = [e['Close'] for e in sdata]
        lows = [e['Low'] for e in sdata]
        highs = [e['High'] for e in sdata]
        ret = PriceSignals().Bottom_Up(openPrices, closePrices, lows, highs)
        assert (ret == True)


class TestPriceSignals(TestCase):
    def test_New_High(self):
        sym = 'PCG'
        date = '2016-06-02'
        data, missing = USMarket([sym], date).getData()
        sdata = data[sym]
        ret = PriceSignals().New_High(sdata)
        assert (ret == True)
