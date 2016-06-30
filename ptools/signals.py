"""
Package for generating signals based on calculated metrics
for example, MACD bullish divergence is based on close prices and MACD-H
closePrices[0] is the most recent price
"""

from ptools import Metrics
from usdata import USMarket

class Signals:
    def __init__(self):
        self.m = Metrics()

    """
    #股价创新低,但是绿柱子(在负数区间)明显比上一次明显缩短
    #而且低位低于上次绿柱子出现的低位
    #算法
    0. 当前价格必须低于上一个价格, macdh是绿柱子,而且比上一根短
    1. 找出从今到之前的三个区间:
        区间1: 截止至今天的区间,macd-h是负数
        区间2: 之前的一个区间,macd-h是整数
        区间3: 再往前一个拒签,macd-h是负数
        如果找不到这三个区间,那么数据不足,不能继续
    2. 计算区间1到区间3的最低收盘价,当前的价格应该是最低,才能继续
       可以加如下条件进一步过滤结果: 计算三个区间的最高价,今天的价格必须低于最高价20%以上
    3. 计算区间1和区间3的macd-h最小值,如果区间1的最小值大于区间3的, 那么继续
    4. 如果到这里,那么bullish divergence应该成立,返回True
    """
    def MACD_bullish_divergence(self, closePrices):
        dsize = len(closePrices)
        #Step 0
        if closePrices[0] > closePrices[1]:
            return False
        macdh = self.m.macd(closePrices)
        if macdh[0] > 0 or macdh[0] < macdh[1]:
            return False

        #Step 1
        pos = []
        idx = 0
        #Locate end of section 1
        while macdh[idx] <= 0 and idx < dsize:
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)
        #Locate end of section 2
        while macdh[idx] >= 0 and idx < dsize:
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)
        #Locate end of section 3
        while macdh[idx] <= 0 and idx < dsize:
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)
        assert(len(pos) == 3)

        # Step 2
        for i in range(1, pos[2]):
            if closePrices[0] > closePrices[i]:
                return False
        high = max(closePrices[:pos[2]])
        if closePrices[0] > high * 0.8:
            return False

        #Step 3
        low_section_1 = min(macdh[0:pos[1]])
        low_section_3 = min(macdh[pos[1]:pos[2]])
        if low_section_1 < low_section_3:
            return False

        return True

def main():
    watchlist = ['TSLA']
    marketData = USMarket(watchlist, '2016-06-26')
    s = Signals()
    priceHistory, missing = marketData.getData('daily')
    print('missing: '+str(missing))
    for sym in [x for x in watchlist if x not in missing]:
        closePrices = [float(x['Close']) for x in priceHistory[sym]]
        ret = s.MACD_bullish_divergence(closePrices)
        print(sym+ ': '+str(ret))

if __name__ == '__main__' :
    main()