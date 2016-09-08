"""
Package for generating signals that only rely prices
for example, MACD bullish divergence is based on close prices and MACD-H
closePrices[0] is the most recent price
"""

from ptools import Metrics

class PriceSignals:
    def __init__(self):
        self.m = Metrics()

    def Type1_buy_point_MACD_bullish_divergence(self, closePrices):
        macd_all = self.m.macd_all(closePrices)
        if macd_all == None:
            return False

        macd_fast = macd_all['fast']
        macd_slow = macd_all['slow']
        macd_histo = macd_all['histo']
        if max(macd_slow[0], macd_fast[0], macd_histo[0]) > 0:
            return False
        if macd_histo[0] < macd_histo[1]:
            return False

        # MACD底部背离已经出现:
        # 底部背离：依次出现金叉，死叉，金叉。虽然这些叉出现时的价格越来越低，但是对应的macd_fast值越来越高
        # 按照第一类买点的定律，出现第二个金叉时，已经错过了最低买点，所以要求是:
        # 最近一次出现了金叉，死叉，当前
        pos = 0
        while pos < len(closePrices) and macd_histo[pos]<0:
            pos += 1
        if pos == len(closePrices):
            return False
        dead_cross = pos

        pos += 1
        while pos < len(closePrices) and macd_histo[pos]>0:
            pos += 1
        if pos == len(closePrices):
            return False
        gold_cross = pos

        """
        print(str([0, dead_cross, gold_cross]))
        print(str([closePrices[0], closePrices[dead_cross], closePrices[gold_cross]]))
        print(str([macd_fast[0], macd_fast[dead_cross], macd_fast[gold_cross]]))
        """
        #价格更低，但是macd没有更低，这就是一种背离
        if not (closePrices[0] < closePrices[gold_cross] and\
                macd_fast[0] > macd_fast[gold_cross]):
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

    #Note that the 'Open' data of the current day is not reliable, so let's not depend on it
    def Bottom_Up(self, openPrices, closePrices, lows, highs):
        #previous bar must be a nagative bar
        if not (closePrices[1] < openPrices[1]):
            return False
        #current price must be higher than previous close
        if not (closePrices[0] > closePrices[1]):
            return False

        #if any recent close price is higher than ema_5 or ema_10, pass
        #a low price is necessary for profitable reversal
        ema_5  = Metrics().ema(closePrices, 5)
        ema_10 = Metrics().ema(closePrices, 10)
        for idx in range(1, 3):
            if closePrices[idx] > min(ema_5[idx], ema_10[idx]):
                return False

        # look back 300 bars for support and resistence, very old bars are not reliable
        sr = self.m.support_and_resistance(openPrices[:300], closePrices[:300])
        myrange = {'min': lows[1], 'max':max(closePrices[0], highs[1])}
        foundSupport = False
        supportIdx = -1
        for i in range(len(sr['price'])):
            price = sr['price'][i]
            if price > myrange['max']:
                continue
            if price < myrange['min']:
                return False
            idx = sr['idx'][i]
            # 如果之前跌破了找到的这个支撑点，那么这个支撑点已经作废了
            if min(closePrices[2:idx]) < price:
                return False
            foundSupport = True
            supportIdx = idx
            break

        if not foundSupport:
            return False

        prevMax = max(closePrices[1:supportIdx])
        #print(str([supportIdx, prevMax, closePrices[0]]))

        if closePrices[0] > prevMax * 0.9:
            return False

        return True

    def New_High(self, data):
        closePrices = [x['Close'] for x in data]
        highs = [x['High'] for x in data]
        if len(closePrices) < 20:
            return False
        prev_high = max(highs[1:])
        cur_price = closePrices[0]
        #print(str([cur_price, prev_high]))
        if cur_price < prev_high:
            return False

        ema_5 = self.m.ema(closePrices, 5)
        ema_10 = self.m.ema(closePrices, 10)

        # if price increased fast, skip
        limit = 1.02
        if (cur_price > min(ema_5[0], closePrices[1]) * limit) or\
           (ema_5[0] > ema_10[0] * limit):
            return False

        #用支撑线阻力线的位置来判断,价格是否在某区间徘徊
        #如果价格一路上升,是不会有支撑和阻力线的
        openPrices = [x['Open'] for x in data]
        sr = self.m.support_and_resistance(openPrices, closePrices)
        sr_price = sr['price']
        lower_bound = cur_price * 0.95
        count = 0
        for p in range(len(sr_price)):
            if sr_price[p] > lower_bound:
                count += 1
        if count < 2:
            return False

        rsi = self.m.rsi(closePrices)
        if max(rsi[:5]) > 70:
            return False

        macd_all = self.m.macd_all(closePrices)
        macd_fast = macd_all['fast']
        sr_idx = sr['idx']
        if macd_fast[0] < macd_fast[sr_idx[0]]:
            #这是MACD背离
            return False

        return True

    #这个版本是: "整数新高"
    def New_High_Old(self, closePrices, highs):
        if len(closePrices) < 20:
            return False
        prev_high = max(highs[1:])
        cur_price = closePrices[0]
        if cur_price < prev_high:
            return False

        cur_price *= 1.02 #if cur_price is 2% short, print it too, so I can watch it
        if cur_price < 10:
            price_threshold = 1
        elif cur_price < 100:
            price_threshold = 10
        else:
            price_threshold = 100

        if int(closePrices[0] / price_threshold) == int(prev_high / price_threshold):
            return False

        return True
