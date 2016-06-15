#!/usr/bin/env python3

"""
Gathers data for symbols in U.S. market using yahoo-finance and google-finance APIs
Gathered data will stored in JSON-format in a file, to avoid fetching every time.
Every symbol will have 2 data file, one for daily and one for weekly. File name is like:
GOOGL-daily-timestamp, and GOOGL-weekly-timestamp
All data files are grouped with in folder "datafiles-us"
date is in a format like '2001-12-10

Yahoo data for TSLA
daily (from Jan 29 2015 until June 15 2016):
http://real-chart.finance.yahoo.com/table.csv?s=TSLA&a=00&b=29&c=2015&d=05&e=15&f=2016&g=d&ignore=.csv
weekly:
http://real-chart.finance.yahoo.com/table.csv?s=TSLA&a=05&b=29&c=2015&d=05&e=15&f=2016&g=w&ignore=.csv
"""

from yahoo_finance import Share
from googlefinance import getQuotes
from datetime import datetime, timedelta
import os, argparse, fnmatch, pytz

foldername = 'datafiles-us'

def arg_parser():
    parser = argparse.ArgumentParser(description='pstock stock analysis tool in python')
    parser.add_argument('filename', type=str, nargs='*', default=['watchlist.txt'],
                        help='file that contains a list of ticker symbols')
    parser.add_argument('-v', dest='verbose', action='store_true', default=False,
                            help='specify verbose exception information')
    parser.add_argument('-w', dest='run weekly data', action='store_true', default=False,
                            help='analyze weekly charts instead of daily charts')
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

def touchFolder():
    if not os.path.exists(foldername):
        os.makedirs(foldername)

def strWithZero(num):
            s = str(num)
            if len(s) < 2:
                return '0' + s
            return s

def construct_yahoo_link(sym, m1, d1, y1, m2, d2, y2, type):
    #on yahoo, month starts at 00, instead of 01
    m1_z = strWithZero(m1 - 1)
    m2_z = strWithZero(m2 - 1)
    def getChartType(type) :
        return {
            'daily' : 'd',
            'weekly' : 'w',
            'monthly' : 'm'
        }[type]
    tstr = getChartType(type)
    ret = 'http://real-chart.finance.yahoo.com/table.csv?s=' + sym
    ret = ret + '&a=' + m1_z
    ret = ret + '&b=' + str(d1)
    ret = ret + '&c=' + str(y1)
    ret = ret + '&d=' + m2_z
    ret = ret + '&e=' + str(d2)
    ret = ret + '&f=' + str(y2)
    ret = ret + '&g=' + tstr
    ret = ret + '&ignore=.csv'
    return ret

class USMarket:
    def __init__(self, watchlist):
        self.watchlist = watchlist
        self.full_history = {}

    def update_daily(self, sym):
        prev_history_ends = self.get_latest_daily_history_date(sym)
        print(sym+ ' history ends: '+ prev_history_ends)
        last_trading_day = self.get_last_trading_date()
        print(sym+ ' latest trading days: '+ last_trading_day)
        self.update_daily_history(sym, prev_history_ends, last_trading_day)
        return
        cur_time = datetime.now(pytz.timezone('US/Eastern'))
        fpathstub = foldername + '/' + sym + '-daily-'
        if os.path.exists(fpathstub):
            #load what we have already
            self.load_daily_from_file(sym)
        else:
            history_starts = cur_time - timedelta(days = 365)
        self.update_daily_from_web(sym, fpathstub, history_starts, cur_time)

    def get_latest_daily_history_date(self, sym):
        prefix = sym + '-daily-'
        maxdate = '1900-01-01'
        foundFile = False
        for fname in os.listdir(foldername):
            if fnmatch.fnmatch(fname, sym + '*'):
                foundFile = True
                datestr = fname[len(prefix):]
                if datestr > maxdate:
                    maxdate = datestr
        if foundFile:
            return maxdate
        # otherwise, let's start from one year ago
        oneYearAgo = datetime.now(pytz.timezone('US/Eastern')) - timedelta(days = 366)
        return '-'.join([strWithZero(x) for x in [oneYearAgo.year, oneYearAgo.month, oneYearAgo.day]])

    def get_last_trading_date(self):
        GOOGL = Share('GOOGL')
        # get_trade_datetime returns the 'last' trading date, which is most-recent-date - 1
        timestr = GOOGL.get_trade_datetime()
        return timestr.split()[0]

    # download .csv file for sym from yahoo finance
    # starting on prev_history_ends + 1
    # ending on last_trading_day
    def update_daily_history(self, sym, prev_history_ends, last_trading_day):
        start = datetime.strptime(prev_history_ends, '%Y-%m-%d') + timedelta(days = 1)
        end = datetime.strptime(last_trading_day, '%Y-%m-%d')
        link = construct_yahoo_link(sym, start.month, start.day, start.year, end.month, end.day, end.year, 'daily')
        print('link: '+link)


    def download_daily_from_yahoo(self, sym, fpathstub, history_starts, cur_time):
        if sym in self.full_history.keys():
            # get the late date in history file
            history_starts = cur_time - timedelta(days = 5)

        history_ends = cur_time

    def load_daily_from_file(self, fpath):
        pass

    def construct_yahoo_link(self, sym, ):
        pass

    def update_weekly(self, sym):
        # fpath = foldername + '/' + sym + '-weekly'
        pass

    def fetchdata(self):
        for sym in self.watchlist:
            self.update_daily(sym)
            self.update_weekly(sym)

def main() :
    args = arg_parser()
    watchlist = read_watchlist(args.filename)
    print(watchlist)

    touchFolder()
    usm = USMarket(watchlist)
    usm.fetchdata()

if __name__ == '__main__' :
    main()