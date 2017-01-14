#!/usr/bin/env python3

import argparse
from usdata import USMarket

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
    for sym in symbols:
        sp = prices[sym]

        # note that sp1[0] is the most recent price point
        pos = 0
        while(sp[pos]['Date'] > buyDate):
            pos+=1

        cost = sp[pos]['Close']
        sell_candidates = [sp[x]['Close'] for x in range(pos)]
        sellPrice = max(sell_candidates)
        gain = sellPrice - cost
        result.append((sym, gain, cost, sellPrice))

    priceSorted = sorted(result, key=lambda tup: tup[1])
    for res in priceSorted:
        print(str(res))

if __name__ == '__main__':
    main()