#!/usr/bin/env python3

import argparse
from usdata import USMarket
from pstrategy import ChartPatterns, TripleScreen

def arg_parser():
    parser = argparse.ArgumentParser(description='pstock stock analysis tool in python')
    parser.add_argument('filename', type=str, nargs='*', default=['watchlist.txt'],
                        help='file that contains a list of ticker symbols')
    parser.add_argument('-d', dest='date', default=None,
                        help='ending date of history data for backtesting')
    parser.add_argument('-s', dest='symbol',
                        help='check one specified symbol, avoid reading symbols from file')
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

def print_progress(msg):
    print('[PROGRESS] '+msg)

def test():
    watchlist = ['USO']
    marketData = USMarket(watchlist, '2016-04-05')
    dataset, missing = marketData.getData('daily')
    symset = [sym for sym in watchlist if sym not in missing]
    cp = ChartPatterns(symset, dataset)
    cp.run()

def main() :
    args = arg_parser()
    if args.symbol != None:
        watchlist = [args.symbol]
    else:
        watchlist = read_watchlist(args.filename)

    if args.date != None:
        marketData = USMarket(watchlist, args.date)
    else:
        marketData = USMarket(watchlist)


    # print_progress('requesting daily data')
    daily, missing_daily = marketData.getData('daily')
    # print_progress('requesting weekly data')
    weekly, missing_weekly = marketData.getData('weekly')
    all_missing = set(missing_daily) | set(missing_weekly)
    if len(all_missing) > 0:
        print('symbols missing data: ' + str(all_missing))
    symlist = [sym for sym in watchlist if sym not in all_missing]

    print(' ----------- ChartPatterns Weekly -------------')
    cp_weekly = ChartPatterns(symlist, weekly)
    cp_weekly.run()

    print(' ----------- ChartPatterns Daily  -------------')
    cp_daily = ChartPatterns(symlist, daily)
    cp_daily.run()

    # print(' ----------- TripleScreen Screen (2 screens)---')
    # ts = TripleScreen(symlist, weekly, daily)
    # decision = ts.run()
    # longStr = shortStr = '(None)'
    # if decision['long'] != None and len(decision['long']) > 0:
    #     longStr = ' '.join(decision['long'])
    # if decision['short'] != None and len(decision['short']) > 0:
    #     shortStr = ' '.join(decision['short'])
    # print('long: '+ longStr)
    # print('short: '+ shortStr)

if __name__ == '__main__' :
    # test()
    main()
