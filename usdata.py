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
from googlefinance import getQuotes as gQuotes
from datetime import datetime, timedelta
import csv, os, argparse, fnmatch, pytz, urllib
import ptools

from pstock import TA

foldername = 'datafiles-us'

# update this field periodically
futureholidays = ['2016-07-04', '2016-09-05', '2016-11-24', '2016-12-25', '2016-12-26',
                  '2017-01-01', '2017-01-16']

def arg_parser():
    parser = argparse.ArgumentParser(description='pstock stock analysis tool in python')
    parser.add_argument('filename', type=str, nargs='*', default=['watchlist.txt'],
                        help='file that contains a list of ticker symbols')
    parser.add_argument('-v', dest='verbose', action='store_true', default=False,
                            help='specify verbose exception information')
    parser.add_argument('-w', dest='frequency', default='daily',
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

def touchFolder():
    if not os.path.exists(foldername):
        os.makedirs(foldername)

def strWithZero(num):
            s = str(num)
            if len(s) < 2:
                return '0' + s
            return s

# get 'current' new york time
# If we are in the morning before market open, 9:30am, use 23:00 of previous day as 'current'.
# So that 'current' always points to a time that has meaningful 'open', 'close' and other data
def get_cur_time():
    cur_time = datetime.now(pytz.timezone('US/Eastern'))
    # if right now is earlier than 9:30am, use 23:30 of previous day as the latest time
    minutes = cur_time.hour * 60 + cur_time.minute
    if minutes < 9 * 60 + 30:
        cur_time = cur_time - timedelta(minutes = (minutes + 60))
    return cur_time

def get_last_trading_date():
    cur_time = get_cur_time()
    #find the most recent trading day if not today
    while True:
        wd = cur_time.weekday()
        if wd == 0 or wd == 6: #Sunday or #Saturday
            cur_time = cur_time - timedelta(days = 1)
            continue

        ts = '-'.join([str(cur_time.year), strWithZero(cur_time.month), strWithZero(cur_time.day)])
        if ts in futureholidays:
            cur_time = cur_time - timedelta(days = 1)
            continue

        break
    prev_day = cur_time - timedelta(days = 1)
    ret = '-'.join([str(prev_day.year), strWithZero(prev_day.month), strWithZero(prev_day.day)])
    return ret

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
    def __init__(self, watchlist, frequency):
        self.watchlist = watchlist
        self.full_history = {}
        self.frequency = frequency

    def update_daily(self, sym):
        prev_history_ends = self.get_latest_daily_history_date(sym)
        last_trading_day = get_last_trading_date()
        self.update_daily_history(sym, prev_history_ends, last_trading_day)
        self.load_daily_from_file(sym)
        self.fetch_current_data(sym)
        pass

    def get_latest_daily_history_date(self, sym):
        prefix = sym + '-daily-'
        maxdate = '1900-01-01'
        foundFile = False
        for fname in os.listdir(foldername):
            if fnmatch.fnmatch(fname, prefix + '*'):
                foundFile = True
                datestr_no_prefix = fname[len(prefix):]
                datestr = datestr_no_prefix[:len(maxdate)] #remove suffix '.csv'
                if datestr > maxdate:
                    maxdate = datestr
        if foundFile:
            return maxdate
        # otherwise, let's start from one year ago
        oneYearAgo = datetime.now(pytz.timezone('US/Eastern')) - timedelta(days = 366)
        return '-'.join([strWithZero(x) for x in [oneYearAgo.year, oneYearAgo.month, oneYearAgo.day]])

    # download .csv file for sym from yahoo finance
    # starting on prev_history_ends + 1
    # ending on last_trading_day
    def update_daily_history(self, sym, prev_history_ends, last_trading_day):
        start = datetime.strptime(prev_history_ends, '%Y-%m-%d') + timedelta(days = 1)
        end = datetime.strptime(last_trading_day, '%Y-%m-%d')
        link = construct_yahoo_link(sym, start.month, start.day, start.year, end.month, end.day, end.year, 'daily')
        localfpath = os.path.join(foldername, sym+'-daily-'+last_trading_day+'.csv')
        try:
            urllib.request.urlretrieve(link, localfpath)
        except:
            pass

    def load_daily_from_file(self, sym):
        self.full_history[sym] = {}
        prefix = sym + '-daily-'
        foundFile = False
        for fname in os.listdir(foldername):
            if fnmatch.fnmatch(fname, prefix + '*'):
                foundFile = True
                localfpath = os.path.join(foldername, fname)
                with open(localfpath) as csvfile:
                    reader = csv.DictReader(csvfile)
                    for datapoint in reader:
                        self.full_history[sym][datapoint['Date']] = datapoint
                    csvfile.close()
        assert(foundFile)


    def fetch_current_data(self, sym):
        sdata = Share(sym)
        cur_time = get_cur_time()
        ts = '-'.join([str(cur_time.year), strWithZero(cur_time.month), strWithZero(cur_time.day)])
        self.full_history[sym][ts] = \
        t = {}
        t['Date']  = '3000-01-01' #debugging purposes, so we know this is current. This won't be saved to file
        t['High']  = sdata.get_days_high()
        t['Low']   = sdata.get_days_low()
        t['Open']  = sdata.get_open()
        # t['Close'] = sdata.get_price()
        t['Close'] = gQuotes(sym)[0]['LastTradePrice'] # use google data for latest 'Close', which is more accurate

    def construct_yahoo_link(self, sym, ):
        pass

    def update_weekly(self, sym):
        # fpath = foldername + '/' + sym + '-weekly'
        pass

    def fetchdata(self):
        if self.frequency == 'daily':
            for sym in self.watchlist:
                self.update_daily(sym)

        elif self.frequency == 'weekly':
            for sym in self.watchlist:
                self.update_weekly(sym)


def main() :
    args = arg_parser()
    watchlist = read_watchlist(args.filename)
    print(watchlist)

    touchFolder()
    usm = USMarket(watchlist, args.frequency)
    usm.fetchdata()

    dateSorted = {}
    for sym in watchlist:
        dateSorted[sym] = [usm.full_history[sym][date] for date in sorted(usm.full_history[sym].keys(), reverse=True)]

    ta = TA(watchlist, dateSorted, True)
    ta.calculations()
    ta.print_results()
    pass

if __name__ == '__main__' :
    main()