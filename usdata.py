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

def get_latest_trading_date(s = None):
    if s == None:
        cur_time = get_cur_time()
    else:
        cur_time = s
    #find the most recent trading day if not today
    while True:
        wd = cur_time.weekday()
        if wd == 5 or wd == 6: #Saturday or Sunday
            cur_time = cur_time - timedelta(days = 1)
            continue

        ts = '-'.join([str(cur_time.year), strWithZero(cur_time.month), strWithZero(cur_time.day)])
        if ts in futureholidays:
            cur_time = cur_time - timedelta(days = 1)
            continue

        break
    ret = '-'.join([str(cur_time.year), strWithZero(cur_time.month), strWithZero(cur_time.day)])
    return ret

def get_monday_of_the_week(dateStr):
    date = datetime.strptime(dateStr, '%Y-%m-%d')
    wd = date.weekday()
    date = date - timedelta(days = wd)
    return '-'.join([str(date.year), strWithZero(date.month), strWithZero(date.day)])

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

def load_csv_from_files(prefix):
    foundFile = False
    ret = {}
    for fname in os.listdir(foldername):
        if fnmatch.fnmatch(fname, prefix + '*'):
            foundFile = True
            localfpath = os.path.join(foldername, fname)
            with open(localfpath) as csvfile:
                reader = csv.DictReader(csvfile)
                for datapoint in reader:
                    ret[datapoint['Date']] = datapoint
                csvfile.close()
    assert(foundFile)
    return ret

class USMarket:
    def __init__(self, watchlist):
        self.watchlist = watchlist
        self.datasets_daily = {}
        self.datasets_weekly = {}

    def update_daily(self, sym):
        if len(self.datasets_daily) != 0:
            return
        prev_history_ends = self.get_latest_history_date(sym)
        latest_trading_date = get_latest_trading_date()
        assert(prev_history_ends <= latest_trading_date)
        if prev_history_ends < latest_trading_date:
            self.download_most_recent_daily(sym, prev_history_ends, latest_trading_date)
        self.load_daily_from_file(sym)
        self.fetch_current_data(sym)

    # download .csv file for sym from yahoo finance
    # starting on prev_history_ends + 1
    # ending on latest_trading_date
    def download_most_recent_daily(self, sym, prev_history_ends, latest_trading_date):
        start = datetime.strptime(prev_history_ends, '%Y-%m-%d') + timedelta(days = 1)
        end = datetime.strptime(latest_trading_date, '%Y-%m-%d')
        link = construct_yahoo_link(sym, start.month, start.day, start.year, end.month, end.day, end.year, 'daily')
        localfpath = os.path.join(foldername, sym+'-daily-'+latest_trading_date+'.csv')
        try:
            urllib.request.urlretrieve(link, localfpath)
        except:
            pass

    def load_daily_from_file(self, sym):
        self.datasets_daily[sym] = load_csv_from_files(sym + '-daily-')

    def fetch_current_data(self, sym):
        sdata = Share(sym)
        ts = get_latest_trading_date(get_cur_time())
        if ts in self.datasets_daily[sym].keys():
            return
        self.datasets_daily[sym][ts] = t = {}
        t['Date']  = '3000-01-01' #debugging purposes, so we know this is current. This won't be saved to file
        t['High']  = sdata.get_days_high()
        t['Low']   = sdata.get_days_low()
        t['Open']  = sdata.get_open()
        # t['Close'] = sdata.get_price()
        t['Close'] = gQuotes(sym)[0]['LastTradePrice'] # use google data for latest 'Close', which is more accurate

    def update_weekly(self, sym):
        if len(self.datasets_weekly) != 0:
            return
        self.update_daily(sym) #data of current week comes from weekly daily data
        prev_history_ends = self.get_latest_history_date(sym, 'weekly')
        latest_trading_date = get_latest_trading_date()
        assert(prev_history_ends <= latest_trading_date)
        if prev_history_ends < latest_trading_date:
            self.download_most_recent_weekly(sym, prev_history_ends, latest_trading_date)
        self.load_weekly_from_file(sym)


    def download_most_recent_weekly(self, sym, prev_history_ends, latest_trading_date):
        #start is the 'next' Monday
        start = datetime.strptime(get_monday_of_the_week(prev_history_ends), '%Y-%m-%d') + \
                timedelta(days = 7)
        end = datetime.strptime(latest_trading_date, '%Y-%m-%d')
        endingMonday = get_monday_of_the_week(latest_trading_date)
        link = construct_yahoo_link(sym, start.month, start.day, start.year, end.month, end.day, end.year, 'weekly')
        localfpath = os.path.join(foldername, sym+'-weekly-'+endingMonday+'.csv')
        try:
            urllib.request.urlretrieve(link, localfpath)
        except:
            pass

    def load_weekly_from_file(self, sym):
        self.datasets_weekly[sym] = load_csv_from_files(sym + '-weekly-')

    def fetchdata(self, frequency = 'daily'):
        touchFolder()
        if frequency == 'daily':
            for sym in self.watchlist:
                self.update_daily(sym)

        elif frequency == 'weekly':
            for sym in self.watchlist:
                self.update_weekly(sym)

    def getData(self, frequency = 'daily'):
        self.fetchdata(frequency)
        sortedByDate = {}
        # return an array (instead of dict)
        # [0] is the most recent price point
        for sym in self.watchlist:
            sortedByDate[sym] = [self.datasets_daily[sym][date] for date in sorted(self.datasets_daily[sym].keys(), reverse=True)]
        return sortedByDate

    def get_latest_history_date(self, sym, frequency='daily'):
        prefix = sym + '-' + frequency + '-'
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
        # otherwise, let's start from a fixed time ago
        longBefore = datetime.now(pytz.timezone('US/Eastern')) - timedelta(days = 712)
        return '-'.join([strWithZero(x) for x in [longBefore.year, longBefore.month, longBefore.day]])

def test_weekly_data():
    watchlist = ['TSLA']
    usm = USMarket(watchlist)
    usm.fetchdata('weekly')
    usm.fetchdata('weekly')

def main() :
    test_weekly_data()
    # args = arg_parser()
    # watchlist = read_watchlist(args.filename)
    # print(watchlist)
    #
    # usm = USMarket(watchlist, args.frequency)
    # usm.fetchdata()

    # dateSorted = {}
    # for sym in watchlist:
    #     dateSorted[sym] = [usm.datasets_daily[sym][date] for date in sorted(usm.datasets_daily[sym].keys(), reverse=True)]
    #
    # ta = TA(watchlist, dateSorted, True)
    # ta.calculations()
    # ta.print_results()

if __name__ == '__main__' :
    main()