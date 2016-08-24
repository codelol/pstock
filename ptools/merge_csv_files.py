#!/usr/bin/env python3

import argparse, os, fnmatch, csv, shutil
from tqdm import tqdm

def arg_parser():
    parser = argparse.ArgumentParser(description='extract symbols listed in a csv file')
    parser.add_argument('folder', type=str, nargs='+',
                        help='folder name wihin which you want to merge csv files')
    args = parser.parse_args()
    return args

def touchFolder(foldername):
    if not os.path.exists(foldername):
        os.makedirs(foldername)

def merge_one_symbol(source_folder, destfolder, sym, frequency):
    data = {}
    prefix = sym + '-' + frequency + '-'
    source_sub_folder = os.path.join(source_folder, sym[:1])
    for fname in os.listdir(source_sub_folder):
        if fnmatch.fnmatch(fname, prefix + '*'):
            localfpath = os.path.join(source_sub_folder, fname)
            with open(localfpath) as csvfile:
                reader = csv.DictReader(csvfile)
                for datapoint in reader:
                    data[datapoint['Date']] = datapoint
                csvfile.close()
    if len(data) == 0:
        return

    destSubFolder = os.path.join(destfolder, sym[:1])
    touchFolder(destSubFolder)

    maxdate = max(data.keys())
    # fieldnames = list(data[maxdate].keys())
    fieldnames = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    fname = prefix + maxdate + '.csv'
    fpath = os.path.join(destSubFolder, fname)
    with open(fpath, 'w') as csvout:
        writer = csv.DictWriter(csvout, fieldnames=fieldnames, extrasaction='raise')
        writer.writeheader()
        keys = sorted(data.keys(), reverse = True)
        for k in keys:
            writer.writerow(data[k])
    csvout.close()

def merge_one_folder(folder):
    folder = folder.rstrip(os.path.sep)
    symlist = []
    for subfolder in os.listdir(folder):
        path = os.path.join(folder, subfolder)
        files = os.listdir(path)
        dailyfiles = [f for f in files if 'daily' in f]
        for fname in dailyfiles:
            sym = fname.split('-')[0]
            if sym not in symlist:
                symlist.append(sym)
    print(str(symlist))
    if len(symlist) == 0:
        return
    tmpfoldername = folder + '_tmp'
    touchFolder(tmpfoldername)
    for sym in tqdm(symlist, desc='Symbol files', unit=' Symbol'):
        merge_one_symbol(folder, tmpfoldername, sym, 'daily')
        merge_one_symbol(folder, tmpfoldername, sym, 'weekly')

    shutil.rmtree(folder, ignore_errors=True)
    os.rename(tmpfoldername, folder)

def main():
    args = arg_parser()
    folders = args.folder

    for folder in folders:
        merge_one_folder(folder)

def test():
    merge_one_folder('tmp/')

if __name__ == '__main__':
    main()
    # test()
