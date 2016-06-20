#!/usr/bin/env python3

import argparse
from usdata import USMarket
from pstrategy import ChartPatterns

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


def main() :
    args = arg_parser()

    watchlist = read_watchlist(args.filename)
    print(watchlist)
    marketData = USMarket(watchlist)

    cp = ChartPatterns(watchlist, marketData.getData('daily'), args.verbose, False)
    cp.run()

if __name__ == '__main__' :
    main()
