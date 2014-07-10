"""
	Date utilities

	Sirguey-Hancock, Ltd.
"""
import time
import os
import datetime

def month_str3_to_int(three_char_month):
    """ Supply a three character month and return the integer of the month. """
    try:
        mth = three_char_month
        mth = mth.lower()

        dic = {}
        dic['jan'] = 1
        dic['feb'] = 2
        dic['mar'] = 3
        dic['apr'] = 4
        dic['may'] = 5
        dic['jun'] = 6
        dic['jul'] = 7
        dic['aug'] = 8
        dic['sep'] = 9
        dic['oct'] = 10
        dic['nov'] = 11
        dic['dec'] = 12

        return dic[mth]
    except Exception as e:
        raise e


def month_int_to_str(int_month):
    """ Convert integer month to January, February, etc. """
    try:
        mth = int_month
        if not isinstance(mth,int):
            raise ValueError('monthToString(m) requires an int as an argument.')

        if mth < 1 or mth > 12:
            raise ValueError('Month integer must be in range 1-12: %d' % mth)

        dic = {}
        dic[1] = 'January'
        dic[2] = 'February'
        dic[3] ='March'
        dic[4] = 'April'
        dic[5] = 'May'
        dic[6] ='June'
        dic[7] ='July'
        dic[8] = 'August'
        dic[9] = 'September'
        dic[10] = 'October'
        dic[11] = 'November'
        dic[12] = 'December'

        return dic[mth]
    except ValueError as e:
        raise e


def month_int_to_str3(int_month):
    """ 
    Convert integer month to Jan, Feb, Mar, etc.
    """
    try:
        mth = int_month
        if not isinstance(mth,int):
            raise ValueError('monthToString(m) requires an int as an argument.')

        if mth < 1 or mth > 12:
            raise ValueError('Month integer must be in range 1-12: %d' % mth)

        dic = {}
        dic[1] = 'Jan'
        dic[2] = 'Feb'
        dic[3] ='Mar'
        dic[4] = 'Apr'
        dic[5] = 'May'
        dic[6] ='Jun'
        dic[7] ='Jul'
        dic[8] = 'Aug'
        dic[9] = 'Sep'
        dic[10] = 'Oct'
        dic[11] = 'Nov'
        dic[12] = 'Dec'

        return dic[mth]
    except Exception as e:
        raise e


def add_ext_time(fname):
    """ Add time extension to a file and return the new filename """
    y, m, d, h, m, s, ms, doy, x = time.localtime()
    ext	= '%d_%d_%d_%d_%d_%d_%d' % (y, m, d, h, m, s, ms)
    path, f = os.path.split(fname)
    return os.path.join(path, '%s.%s' % (f, ext))


def month3_char_valid(char3_month):
    """ Is this a valid three character month string. """
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    return char3_month.lower() in months


def lastDayOfMonth(yr, numMonth):
    """ Pass the number of the month and return the last day of the month. """
    n = numMonth
    year = yr
    lastDay = 0

    if n ==1 or n == 3 or n == 5 or n == 7 or n == 8 or n == 10 or n == 12:
        lastDay = 31
    elif n == 4 or n == 6 or n == 9 or n == 11:
        lastDay = 30
    elif n == 2 and isLeap(year):
        lastDay = 29
    elif n == 2 and not isLeap(year):
        lastDay = 28

    return lastDay


def isLeap(year):
    """ Return true if is leap year. """
    if year % 400 == 0 or year % 4 == 0:
        return True

    return False

class Parser:
    """ map month abbreviations to month numbers. """
    _month_numbers = {
        'jan':  1, 'feb':  2, 'mar':  3, 'apr':  4,
        'may':  5, 'jun':  6, 'jul':  7, 'aug':  8,
        'sep':  9, 'oct': 10, 'nov': 11, 'dec': 12}

    def __init__(self):
        pass

    def parse_date_to_epoch_seconds(self, month_abbreviation, day, year_or_time):
        """ Return a float of epoch seconds from a string
        time consisting of a three letter month abbreivation,
        a digit day, and year or time.
        """
        try:
            month = self._month_numbers[month_abbreviation.lower()]
        except KeyError:
            raise KeyError("invalid month name '%s'" % month)

        try:
            day = int(day)
        except ValueError:
            raise ValueError('%s cannot be converted to type in' % day)

        if ":" not in year_or_time:
            # `year_or_time` is really a year
            year, hour, minute = int(year_or_time), 0, 0
            st_mtime = time.mktime( (year, month, day,
                                     hour, minute, 0, 0, 0, -1) )
        else:
            # `year_or_time` is a time hh:mm
            hour, minute, sconds = year_or_time.split(':')
            year, hour, minute = None, int(hour), int(minute)
            # try the current year
            year = time.localtime()[0]
            st_mtime = time.mktime( (year, month, day,
                                     hour, minute, 0, 0, 0, -1) )

        return st_mtime


def covnvert_date_time_strings_to_datetime(d, t):
    """ Convert strings mm/dd/yyyy and hh:mm to a datetime object."""
    date_string = d
    time_string = t
    date_format_err = 'date_string must be in the format mm/dd/yyyy'
    time_format_err = 'time_string must be in the format hh:mm 24-hour format.'

    if '/' not in date_string:
        raise ValueError(date_format_err)

    if ':' not in time_string:
        raise ValueError(time_format_err)


    date_parts = date_string.split('/')
    if len(date_parts) != 3:
        raise ValueError(date_format_err)

    m = date_parts[0]
    d = date_parts[1]
    y = date_parts[2]

    try:
        int_m = int(m)
        int_d = int(d)
        int_y = int(y)
    except ValueError as e:
        raise e

    time_parts = time_string.split(':')
    if len(time_parts ) != 2:
        raise ValueError(time_format_err)

    hh = time_parts[0]
    mm = time_parts[1]

    try:
        int_hh = int(hh)
        int_mm = int(mm)
    except ValueError as e:
        raise e

    return datetime.datetime(int_y, int_m, int_d, int_hh, int_mm)


def convert_datetime_strings_to_epoch_secs(dat, tim):
    """ Convert strings mm/dd/yyyy and hh:mm to epoch seconds."""
    try:
        dt = covnvert_date_time_strings_to_datetime(dat, tim)
        es = convert_datetime_to_epoch_secs(dt)
    except Exception as e:
        raise e

    return es


def convert_datetime_to_epoch_secs(dt):
    """ Convert datetime object to epoch seconds."""
    try:
        dt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute)
        es = time.mktime(dt.timetuple())
    except Exception as e:
        raise e

    return es


def current_time_epoch_secs():
    """ current ime in epoch seconds.	"""
    try:
        today = datetime.datetime.today()
        es =  time.mktime(today.timetuple())
    except Exception as e:
        raise e

    return es