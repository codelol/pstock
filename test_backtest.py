from unittest import TestCase
from backtest import backtester


class TestBacktest(TestCase):
    def test_backtest(self):
        symbols = ['TSLA']
        buyDate = '2017-01-01'
        sellUntil = '2017-01-14'
        backtester(symbols, buyDate, sellUntil)
