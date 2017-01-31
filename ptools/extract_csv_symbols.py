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
                mcstr = datapoint['MarketCap']
                if mcstr == 'n/a':
                    continue
                if mcstr[len(mcstr)-1] == 'B':
                    mcstr = mcstr[:len(mcstr)-1]
                elif mcstr[len(mcstr)-1] == 'M': #market cap is not at billion level, skip this one
                    continue
                if mcstr[0] == '$':
                    mcstr = mcstr[1:]
                marketCap = float(mcstr)
                if marketCap < minMarketCap:
                    continue
                if maxMarketCap > 0 and marketCap > maxMarketCap:
                    continue
                sym = datapoint['Symbol']
                all_symbols.append(sym)
                print(sym)

if __name__ == '__main__' :
    main()
