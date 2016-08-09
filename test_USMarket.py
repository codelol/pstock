from unittest import TestCase
from usdata import USMarket

class TestUSMarket(TestCase):
    def test_getData(self):
        watchlist = ['AAPL']
        # usm = USMarket(watchlist, '2016-01-04')
        usm = USMarket(watchlist)
        daily, missing1 = usm.getData('daily')
        weekly, missing2 = usm.getData('weekly')
        print(str(daily))
        print(str(weekly))
