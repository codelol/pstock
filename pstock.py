#!/usr/bin/env python3

import argparse
from usdata import USMarket
from pstrategy import ChartPatterns, TripleScreen

def arg_parser():
    parser = argparse.ArgumentParser(description='pstock stock analysis tool in python')
    parser.add_argument('filename', type=str, nargs='*', default=['watchlist.txt'],
                        help='file that contains a list of ticker symbols')
    parser.add_argument('-v', dest='verbose', action='store_true', default=False,
                            help='specify verbose exception information')
    parser.add_argument('-q', dest='frequency', default='daily',
                            help='daily (default), weekly or monthly data')
    args = parser.parse_args()
    return args;

def read_watchlist(files) :
    ret = []
    for f in files:
        for line in open(f, 'r'):
            if line[0] == '#':
                continue
            ret.append(line.strip())
    return ret

def format_red(str):
    return("\033[91m{}\033[0m".format(str))

def print_red(str):
    print(format_red(str))

def test():
    watchlist = ['BABA']
    marketData = USMarket(watchlist)
    dataset, missing = marketData.getData('daily')
    symset = [sym for sym in watchlist if sym not in missing]
    cp = ChartPatterns(symset, dataset, False, False)
    cp.run()

def main() :
    args = arg_parser()

    watchlist = read_watchlist(args.filename)
    print(watchlist)
    marketData = USMarket(watchlist)
    # dataset, missing = marketData.getData(args.frequency)
    # symset = [sym for sym in watchlist if sym not in missing]
    # cp = ChartPatterns(symset, dataset, args.verbose, False)
    # cp.run()

    daily, missing1 = marketData.getData('daily')
    weekly, missing2 = marketData.getData('weekly')
    all_missing = set(missing1) | set(missing2)
    if len(all_missing) > 0:
        print('symbols missing data: ' + str(all_missing))

    symlist = [sym for sym in watchlist if sym not in all_missing]
    ts = TripleScreen(symlist, weekly, daily)
    decision = ts.run()
    print('long: '+str(decision['long']))
    print('short: '+str(decision['short']))

if __name__ == '__main__' :
    main()
