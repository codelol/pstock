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
from tqdm import tqdm
from ptools import WorkPool
import csv, os, argparse, fnmatch, pytz, urllib

foldername = 'datafiles-us'
max_history_year=5 #if no history data exists, download the last 5 years of history

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

def get_friday_of_the_week(dateStr):
    date = datetime.strptime(get_monday_of_the_week(dateStr), '%Y-%m-%d')
    date = date + timedelta(days = 4)
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

def load_csv_from_files(prefix, endingDate = None):
    ret = {}
    for fname in os.listdir(foldername):
        if fnmatch.fnmatch(fname, prefix + '*'):
            foundFile = True
            localfpath = os.path.join(foldername, fname)
            with open(localfpath) as csvfile:
                reader = csv.DictReader(csvfile)
                for datapoint in reader:
                    dt = datapoint['Date']
                    if endingDate is None or dt <= endingDate:
                        ret[dt] = datapoint
                        ret[dt]['Open'] = float(datapoint['Open'])
                        ret[dt]['Close'] = float(datapoint['Close'])
                        ret[dt]['Low'] = float(datapoint['Low'])
                        ret[dt]['High'] = float(datapoint['High'])
                        ret[dt]['Volume'] = float(datapoint['Volume'])
                csvfile.close()
    return ret

class USMarket:
    def __init__(self, watchlist, endDate = '9999-99-99'):
        self.watchlist = watchlist
        self.endDate = endDate
        self.adjusted_endDate = get_latest_trading_date(
            datetime.strptime(endDate, '%Y-%m-%d')
        ) if endDate != '9999-99-99' else '9999-99-99'
        self.datasets_daily = {}
        self.datasets_weekly = {}
        self.missing_daily = []
        self.missing_weekly = []
        self.daily_data_updated = False

    def update_daily(self, sym):
        if self.daily_data_updated:
            return
        try:
            self.load_daily_from_file(sym)
            prev_history_ends = self.get_latest_history_date(sym)
            latest_trading_date = get_latest_trading_date()
            assert(prev_history_ends <= latest_trading_date)
            ending = min(self.adjusted_endDate, latest_trading_date)
            if prev_history_ends < ending:
                self.download_most_recent_daily(sym, prev_history_ends, ending)
                self.fetch_current_data(sym)
        except:
            if sym not in self.missing_daily:
                self.missing_daily.append(sym)

    def load_daily_from_file(self, sym):
        self.datasets_daily[sym] = load_csv_from_files(sym + '-daily-', self.adjusted_endDate)

    # download .csv file for sym from yahoo finance
    # starting on prev_history_ends + 1
    # ending on latest_trading_date
    def download_most_recent_daily(self, sym, prev_history_ends, latest_trading_date):
        start = datetime.strptime(prev_history_ends, '%Y-%m-%d') + timedelta(days = 1)
        end = datetime.strptime(latest_trading_date, '%Y-%m-%d')
        link = construct_yahoo_link(sym, start.month, start.day, start.year, end.month, end.day, end.year, 'daily')
        fname = sym+'-daily-'+latest_trading_date+'.csv'
        localfpath = os.path.join(foldername, fname)
        try:
            urllib.request.urlretrieve(link, localfpath)
            maxdate = '0000-00-00'
            with open(localfpath) as csvfile:
                reader = csv.DictReader(csvfile)
                for datapoint in reader:
                    dateStr = datapoint['Date']
                    if dateStr > maxdate:
                        maxdate = dateStr
                    self.datasets_daily[sym][dateStr] = datapoint
                    self.datasets_daily[sym][dateStr]['Open'] = float(datapoint['Open'])
                    self.datasets_daily[sym][dateStr]['Close'] = float(datapoint['Close'])
                    self.datasets_daily[sym][dateStr]['Low'] = float(datapoint['Low'])
                    self.datasets_daily[sym][dateStr]['High'] = float(datapoint['High'])
                    self.datasets_daily[sym][dateStr]['Volume'] = float(datapoint['Volume'])
            if maxdate != '0000-00-00' and maxdate != latest_trading_date:
                new_fname = sym+'-daily-'+maxdate+'.csv'
                new_localfpath = os.path.join(foldername, new_fname)
                os.rename(localfpath, new_localfpath)
        except:
            pass

    def fetch_current_data(self, sym):
        ts = get_latest_trading_date(get_cur_time())
        if ts in self.datasets_daily[sym].keys() or ts > self.endDate:
            return
        try:
            sdata = Share(sym)
            gquote = gQuotes(sym)
        except:
            # live with the fact that data from the most recent day is missing
            return
        self.datasets_daily[sym][ts] = t = {}
        t['Date']  = '3000-01-01' #debugging purposes, so we know this is current. This won't be saved to file
        t['High']  = float(sdata.get_days_high())
        t['Low']   = float(sdata.get_days_low())
        t['Open']  = float(sdata.get_open())
        # t['Close'] = sdata.get_price()
        t['Close'] = float(gquote[0]['LastTradePrice']) # use google data for latest 'Close', which is more accurate
        t['Volume'] = float(sdata.get_volume())
        for k in t.keys():
            if t[k] == None:
                raise Exception('missing most recent daily', sym)

    def update_weekly(self, sym):
        self.update_daily(sym) #data of current week comes from weekly daily data
        if sym in self.missing_daily:
            if sym not in self.missing_weekly:
                self.missing_weekly.append(sym)
            return
        try:
            self.load_weekly_from_file(sym)
            prev_history_ends = get_friday_of_the_week(self.get_latest_history_date(sym, 'weekly'))
            #request weekly data as late as previous Friday to avoid partial weekly data for the current
            interested_ending_date = min(self.adjusted_endDate, get_latest_trading_date())
            prev_friday_date = datetime.strptime(get_friday_of_the_week(interested_ending_date), '%Y-%m-%d') - \
                                timedelta(days = 7)
            prev_friday_str = '-'.join([str(prev_friday_date.year), strWithZero(prev_friday_date.month), \
                                            strWithZero(prev_friday_date.day)])
            ending = prev_friday_str
            if prev_history_ends < ending:
                self.download_most_recent_weekly(sym, prev_history_ends, ending)

            # remove the most recent week of data in case user points to a day in the middle of the week
            # calculate_most_recent_weekly will take of the most recent partial week
            most_recent_monday = get_monday_of_the_week(max(self.datasets_weekly[sym].keys()))
            assert(most_recent_monday in self.datasets_weekly[sym].keys());
            del self.datasets_weekly[sym][most_recent_monday]

            self.calculate_most_recent_weekly(sym)
        except:
            if sym not in self.missing_weekly:
                self.missing_weekly.append(sym)


    def download_most_recent_weekly(self, sym, prev_history_ends, ending):
        #start is the 'next' Monday
        start = datetime.strptime(get_monday_of_the_week(prev_history_ends), '%Y-%m-%d') + \
                timedelta(days = 7)
        #assert that ending is already the correct Friday
        assert(ending == get_friday_of_the_week(ending))
        end = datetime.strptime(ending, '%Y-%m-%d')
        link = construct_yahoo_link(sym, start.month, start.day, start.year, end.month, end.day, end.year, 'weekly')
        endingMonday = get_monday_of_the_week(ending)
        fname = sym+'-weekly-'+endingMonday+'.csv'
        localfpath = os.path.join(foldername, fname)
        try:
            urllib.request.urlretrieve(link, localfpath)
            maxdate = '0000-00-00'
            with open(localfpath) as csvfile:
                reader = csv.DictReader(csvfile)
                for datapoint in reader:
                    dateStr = datapoint['Date']
                    if dateStr > maxdate:
                        maxdate = dateStr
                    self.datasets_weekly[sym][dateStr] = datapoint
                    self.datasets_weekly[sym][dateStr]['Open'] = float(datapoint['Open'])
                    self.datasets_weekly[sym][dateStr]['Close'] = float(datapoint['Close'])
                    self.datasets_weekly[sym][dateStr]['Low'] = float(datapoint['Low'])
                    self.datasets_weekly[sym][dateStr]['High'] = float(datapoint['High'])
                    self.datasets_weekly[sym][dateStr]['Volume'] = float(datapoint['Volume'])
            if maxdate != '0000-00-00' and maxdate != endingMonday:
                new_fname = sym+'-weekly-'+maxdate+'.csv'
                new_localfpath = os.path.join(foldername, new_fname)
                os.rename(localfpath, new_localfpath)
        except:
            pass

    def load_weekly_from_file(self, sym):
        self.datasets_weekly[sym] = load_csv_from_files(sym + '-weekly-')

    def calculate_most_recent_weekly(self, sym):
        most_recent_week = get_monday_of_the_week(max(self.datasets_weekly[sym].keys()))
        current_week_monday = get_monday_of_the_week(max(self.datasets_daily[sym].keys()))
        while True:
            nextweek_Monday = datetime.strptime(most_recent_week, '%Y-%m-%d') + timedelta(days = 7)
            monday_str = '-'.join([strWithZero(x) for x in [nextweek_Monday.year, nextweek_Monday.month, nextweek_Monday.day]])
            if monday_str > current_week_monday:
                break
            found = 0
            for i in range(5):
                day = nextweek_Monday + timedelta(days = i)
                kstr = '-'.join([strWithZero(x) for x in [day.year, day.month, day.day]])
                if kstr in self.datasets_daily[sym].keys():
                    if found == 0:
                        self.datasets_weekly[sym][monday_str] = \
                            {'Date': monday_str,'Open': None, 'Close' : None, 'High' : None, 'Low' : None, 'Volume' : 0}

                    found = found + 1
                    data = self.datasets_weekly[sym][monday_str]
                    if data['Open'] == None:
                        data['Open'] = self.datasets_daily[sym][kstr]['Open']
                    data['Close'] = self.datasets_daily[sym][kstr]['Close']

                    high_float = float(self.datasets_daily[sym][kstr]['High'])
                    if data['High'] == None or high_float > float(data['High']):
                        data['High'] = high_float

                    low_float = float(self.datasets_daily[sym][kstr]['Low'])
                    if data['Low'] == None or low_float < float(data['Low']):
                        data['Low'] = low_float

                    data['Volume'] = float(data['Volume']) + float(self.datasets_daily[sym][kstr]['Volume'])
            if found > 0:
                # volume in weekly chart is 'avg'
                self.datasets_weekly[sym][monday_str]['Volume'] = \
                    str(int(float(self.datasets_weekly[sym][monday_str]['Volume']) / found))
            most_recent_week = monday_str

    def fetchdata(self, frequency = 'daily'):
        touchFolder()
        wpool = WorkPool(10)
        if frequency == 'daily':
            if len(self.datasets_daily) != 0:
                return
            self.missing_daily = []
            for sym in tqdm(self.watchlist, desc='daily chart', unit=' Symbol'):
                wpool.start_work(self.update_daily, sym)
            self.daily_data_updated = True

        elif frequency == 'weekly':
            if len(self.datasets_weekly) != 0:
                return
            self.missing_weekly = []
            for sym in tqdm(self.watchlist, desc='weekly chart', unit=' Symbol'):
                wpool.start_work(self.update_weekly, sym)
        wpool.wait_for_all()

    def getData(self, frequency = 'daily'):
        self.fetchdata(frequency)
        missing = []
        if frequency == 'daily':
            dataset = self.datasets_daily
            missing = self.missing_daily
        elif frequency == 'weekly':
            dataset = self.datasets_weekly
            missing = self.missing_weekly
        sortedByDate = {}
        # return an array (instead of dict)
        # [0] is the most recent price point
        for sym in list(set(self.watchlist) - set(missing)):
            sortedByDate[sym] = [dataset[sym][date] for date in sorted(dataset[sym].keys(), reverse=True) if date <= self.endDate]
        return sortedByDate, missing

    def get_latest_history_date(self, sym, frequency='daily'):
        dates = {}
        if frequency == 'daily':
            dates = sorted(self.datasets_daily[sym].keys(), reverse = True)
        elif frequency == 'weekly':
            dates = sorted(self.datasets_weekly[sym].keys(), reverse = True)

        if len(dates) == 0:
            # if nothing is loaded from file, let's start from a fixed time ago
            longBefore = datetime.now(pytz.timezone('US/Eastern')) - timedelta(days = (max_history_year * 365))
            return '-'.join([strWithZero(x) for x in [longBefore.year, longBefore.month, longBefore.day]])

        return dates[0]
