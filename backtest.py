#!/usr/bin/env python3

import argparse
from usdata import USMarket
from tabulate import tabulate

def arg_parser():
    parser = argparse.ArgumentParser(description='test gains/loss for each given symbol')
    parser.add_argument('symbols', type=str, nargs='+',
                        help='symbols')
    parser.add_argument('-b', dest='buy_Date', type=str, required=True,
                        help='will use close price on this date as cost basis')
    parser.add_argument('-s', dest='sell_until', type=str, required=True,
                        help='assume sold at the best price until this day')
    args = parser.parse_args()
    return args;

def main():
    args = arg_parser()
    symbols = args.symbols
    buyDate = args.buy_Date
    sellUntil = args.sell_until
    backtester(symbols, buyDate, sellUntil)

def backtester(symbols, buyDate, sellUntil) :
    prices, missing = USMarket(symbols, sellUntil).getData('daily')

    skipped = []
    for m in missing:
        symbols.remove(m)
        skipped.append(m)

    result = []
    win = 0
    loss = 0
    worstCaseWin = 0
    worstCaseLoss = 0
    for sym in symbols:
        sp = prices[sym]

        # note that sp1[0] is the most recent price point
        pos = 0
        while(sp[pos]['Date'] > buyDate):
            pos+=1

        cost = sp[pos]['Close']
        sell_candidates = [sp[x]['Close'] for x in range(pos)]

        sellPrice = max(sell_candidates) #suppose we can sell at the highest price within this period
        if sellPrice > cost :
            win += 1
        else :
            loss += 1

        lowestPrice = min(sell_candidates)
        if lowestPrice > cost:
            worstCaseWin += 1
        else :
            worstCaseLoss += 1

        gain = (sellPrice - cost) / cost * 100 #will be used as percentage
        worstCase = (lowestPrice - cost) / cost * 100
        result.append((sym, gain, cost, sellPrice, worstCase))

    gainSorted = sorted(result, key=lambda tup: float(tup[1]), reverse=True)
    printResults(gainSorted, ["Symbol", "%Gain", "Cost", "SellPrice", "%WorstCase"])
    print('BestCase  => Win: ' + str(win) +'; Loss: '+ str(loss) + '; Win rate: %.2f' % round(win/(win+loss), 2))
    print('WorstCase => Win: ' + str(worstCaseWin) +'; Loss: '+ str(worstCaseLoss) + \
          '; Win rate: %.2f' % round(worstCaseWin/(worstCaseWin+worstCaseLoss), 2))

def printResults(result, colNames) :
    print(tabulate(result, colNames, floatfmt=".2f"))

if __name__ == '__main__':
    main()