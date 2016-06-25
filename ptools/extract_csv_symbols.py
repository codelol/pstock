#!/usr/bin/env python3

#link to download the original csv files containing all symbols:
#http://www.nasdaq.com/screening/company-list.aspx

import csv, argparse

def arg_parser():
    parser = argparse.ArgumentParser(description='extract symbols listed in a csv file')
    parser.add_argument('filename', type=str, nargs='*',
                        help='filename of csv file')
    parser.add_argument('-m', dest='minMarketCap', default=0, help='minimum market cap in billion')
    parser.add_argument('-M', dest='maxMarketCap', default=-1, help='maximum market cap in billion')
    args = parser.parse_args()
    return args;

billion = float(1000 * 1000 * 1000)

def main():
    args = arg_parser()
    fnames = args.filename
    if fnames == None or len(fnames) == 0:
        return

    minMarketCap = float(args.minMarketCap)
    maxMarketCap = float(args.maxMarketCap)

    all_symbols = []
    for f in fnames:
        with open(f) as csvfile:
            reader = csv.DictReader(csvfile)
            for datapoint in reader:
                marketCap = float(datapoint['MarketCap'])
                if marketCap < minMarketCap * billion:
                    continue
                if maxMarketCap > 0 and marketCap > maxMarketCap * billion:
                    continue
                sym = datapoint['Symbol']
                all_symbols.append(sym)
                print(sym)

if __name__ == '__main__' :
    main()