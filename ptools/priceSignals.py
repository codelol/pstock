"""
Package for generating signals that only rely prices
for example, MACD bullish divergence is based on close prices and MACD-H
closePrices[0] is the most recent price
"""

from ptools import Metrics
# from usdata import USMarket

class PriceSignals:
    def __init__(self):
        self.m = Metrics()

    """
    #股价创新低,但是绿柱子(在负数区间)明显比上一次明显缩短
    #而且低位低于上次绿柱子出现的低位
    #算法
    0. 当前价格必须低于上一个价格, macdh是绿柱子,而且比上一根短
    1. 找出从今到之前的三个区间:
        区间1: 截止至今天的区间,macd-h是负数
        区间2: 之前的一个区间,macd-h是正数
        区间3: 再往前一个拒签,macd-h是负数
        如果找不到这三个区间,那么数据不足,不能继续
        #如果任何区间的长度少于等于3，那么可以认为是噪音，不考虑
    2. 计算区间1到区间3的最低收盘价,当前的价格应该是最低,才能继续
       可以加如下条件进一步过滤结果: 计算三个区间的最高价,今天的价格必须低于最高价20%以上
    3. 计算区间1和区间3的macd-h最小值,如果区间1的最小值大于区间3的, 那么继续
    4. 如果到这里,那么bullish divergence应该成立,返回True
    """
    def Type1_buy_point_MACD_bullish_divergence(self, closePrices):
        min_sec_len = 3
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
        if idx == dsize or idx <= min_sec_len:
            return False
        pos.append(idx)
        #Locate end of section 2
        while macdh[idx] >= 0 and idx < dsize:
            idx += 1
        if idx == dsize or (idx - pos[len(pos)-1]) <= min_sec_len:
            return False
        pos.append(idx)
        #Locate end of section 3
        while macdh[idx] <= 0 and idx < dsize:
            idx += 1
        if idx == dsize or (idx - pos[len(pos)-1]) <= min_sec_len:
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


    """
    思想:
        在长期的股价低迷之后,出现了突破,短期均线超过长期均线.但是随后出现调整.
        这个调整伴随着缩量, 可能是shorter trap,可以介入.
        因为交易量数据的不准确, 程序中不读取交易量
    算法:
        下列条件必须首先满足, 否则立即返回False:
            最新价格比上一个价格是下降的;
            短期均线(5)在中期均线(10)和长期均线(20)之下
        # 找到三个区间:
            区间1: 从最近的交易开始,往回找,直到短期均线位于中期和长期均线上方
            区间2: 从区间1的分界日开始往回找,往回找,直到短期均线位于中期和长期均线下方
            区间3: 从区间2的分界日开始,往回找,直到短期均线和中期均线均位于长期均线之上
        # 计算区间2的最高价,区间3的最低价, 以及区间3开始的价格(成为最初价)
            区间3的最低价必须低于最初价20%以上,否则不构成"股价低迷"
            区间2的最高价必须高于区间3最低价的5%,否则不成为突破
            如果当前价低于区间2的最高价15%，则是下跌而不是回调
            如果当前价格是三个区间的最低价，则是下跌而不是回调
        # 如果进行到这里,则可以看成是满足条件
    """
    def Type2_buy_point_pullback_after_breakthrough(self, closePrices):
        ema_short = self.m.ema(closePrices, 5)
        ema_mid   = self.m.ema(closePrices, 10)
        ema_long  = self.m.ema(closePrices, 20)
        if closePrices[0] > closePrices[1]:
            return False
        if ema_short[0] > min(ema_mid[0], ema_long[0]):
            return False
        dsize = len(closePrices)
        pos = []
        idx = 0

        #locate end of section 1
        while idx < dsize and ema_short[idx] < max(ema_mid[idx], ema_long[idx]):
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)

        #locate end of section 2
        while idx < dsize and ema_short[idx] > min(ema_mid[idx], ema_long[idx]):
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)

        #locate end of section 3
        while idx < dsize and (ema_short[idx] < max(ema_mid[idx], ema_long[idx]) or ema_mid[idx] < ema_long[idx]) :
            idx += 1
        if idx == dsize:
            return False
        pos.append(idx)

        init_price = closePrices[pos[2]]
        low_section3 = min(closePrices[pos[1]:pos[2]])
        high_section2 = max(closePrices[pos[0]:pos[1]])
        if low_section3 > init_price * 0.8 or high_section2 < low_section3 * 1.05 or \
           closePrices[0] < high_section2 * 0.85:
            return False

        if closePrices[0] < min(closePrices[1:pos[2]]):
            return False

        return True

# def test_type2():
#     watchlist = ['TWTR']
#     marketData = USMarket(watchlist, '2016-06-10')
#     s = PriceSignals()
#     priceHistory, missing = marketData.getData('daily')
#     ret = False
#     for sym in [x for x in watchlist if x not in missing]:
#         closePrices = [float(x['Close']) for x in priceHistory[sym]]
#         ret = s.Type2_buy_point_pullback_after_breakthrough(closePrices)
#     assert(ret)
#
# def main():
#     watchlist = ['TWTR']
#     marketData = USMarket(watchlist, '2016-06-10')
#     s = PriceSignals()
#     priceHistory, missing = marketData.getData('daily')
#     print('missing: '+str(missing))
#     for sym in [x for x in watchlist if x not in missing]:
#         closePrices = [float(x['Close']) for x in priceHistory[sym]]
#         ret = s.Type1_buy_point_MACD_bullish_divergence(closePrices)
#         print(sym+ ': '+str(ret))
#         ret = s.Type2_buy_point_pullback_after_breakthrough(closePrices)
#         print(sym+ ': '+str(ret))
#
# if __name__ == '__main__' :
#     # test_type2()
#     # main()
