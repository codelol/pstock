#!/usr/bin/env python3

#open chrome tabs to open stockchart.com for symbols

import argparse
import subprocess

def arg_parser():
    parser = argparse.ArgumentParser(description='open one google chrome tab for each symbl')
    parser.add_argument('symbols', type=str, nargs='*',
                        help='symbols')
    parser.add_argument('-w', dest='website', default='stockcharts',
                        help='website to check stock price: stockchart or finviz')
    args = parser.parse_args()
    return args;

def main():
    args = arg_parser()
    url = 'http://stockcharts.com/freecharts/gallery.html?'
    if args.website == 'finviz':
        url = 'http://finviz.com/quote.ashx?t='
    symbols = args.symbols
    for sym in symbols:
        subprocess.call(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                         '--new-tab',
                         url+sym])

if __name__ == '__main__':
    main()