#!/usr/bin/env python3

import argparse, os, fnmatch, csv, shutil
from tqdm import tqdm

def arg_parser():
    parser = argparse.ArgumentParser(description='Analyze symbols that appeared more than once')
    parser.add_argument('symbols', type=str, nargs='+',
                        help='folder name wihin which you want to merge csv files')
    args = parser.parse_args()
    return args

def main():
    args = arg_parser()
    syms = args.symbols
    counts = {}
    for s in syms:
        if s in counts.keys():
            counts[s] += 1
        else:
            counts[s] = 1
    results = []
    for i in counts.keys():
        if counts[i] > 1:
            results.append(i)
    print(results)

if __name__ == '__main__':
    main()
