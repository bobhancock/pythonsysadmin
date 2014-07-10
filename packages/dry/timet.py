from datetime import datetime, timedelta
import time
import os
import gzip

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
    if len(time_parts ) < 2:
        raise ValueError(time_format_err)

    hh = time_parts[0]
    mm = time_parts[1]
    if len(time_parts) > 2:
        ss = time_parts[2]

    try:
        int_hh = int(hh)
        int_mm = int(mm)
        int_ss = int(ss)
    except ValueError as e:
        raise e


    dt = datetime(int_y, int_m, int_d, int_hh, int_mm, int_ss)
    return dt


def convert_date_time_strings_to_epoch_secs(dat, tim):
    try:
        dt = covnvert_date_time_strings_to_datetime(dat, tim)
        es = convert_datetime_to_epoch_secs(dt)
    except Exception as e:
        raise e
    
    return es


def convert_datetime_to_epoch_secs(dt):
    " Convert datetime object to epoch seconds."
    try:
        buf = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.microsecond)

        epoch_seconds = time.mktime(buf.timetuple())
    except Exception as e:
        raise e
    
    return epoch_seconds
    

def default_start_date_epoch_secs():
    """ Default dates are yesterday at one second past midnight to current date and time. 
	"""
    try:
        today = datetime.today()
        yesterday_delta = today - timedelta(1)
        yesterday = datetime(yesterday_delta.year, yesterday_delta.month,
                             yesterday_delta.day, 0, 0, 1)

        epoch_seconds_start = time.mktime(yesterday.timetuple())
    except Exception as e:
        raise e

    return epoch_seconds_start


def default_stop_date_epoch_secs():
    """ current date and time. 
	"""
    try:
        today = datetime.today()

        epoch_seconds_stop =  time.mktime(today.timetuple())
    except Exception as e:
        raise e

    return epoch_seconds_stop

def default_start_date_string():
    """ Default date is yesterday. """
    try:
        today = datetime.today()
        yesterday = today - timedelta(1)

        str_month = intMonthToString3(yesterday.month)
        
        string_start = '%s %d %d' % (str_month, yesterday.day, yesterday.year)
    except Exception as e:
        raise e

    return string_start


def default_stop_date_string():
    """ Default dates are yesterday a noon to current date and time. 
	"""
    try:
        today = datetime.today()
        str_month = intMonthToString3(today.month)
        string_stop = '%s %d %d' % (str_month, today.day, today.year)
    except Exception as e:
        raise e

    return string_stop


def default_stop_time_string():
    """ Default dates are yesterday a noon to current date and time. 
	"""
    try:
        today = datetime.today()

        string_stop = '%d:%d:%d' % (today.hour, today.minute, today.second)
    except Exception as e:
        raise e

    return string_stop


def is_file_within_date_range(esStart, esStop, esFileDate):
    """ Does file fall within this date range. """
    try:
        epoch_seconds_start = esStart
        epoch_seconds_stop = esStop
        epoch_seconds_file_date = esFileDate

        if epoch_seconds_file_date >= epoch_seconds_start \
           and epoch_seconds_file_date <= epoch_seconds_stop:
            return True
        else:
            return False
    except Exception as e:
        raise e

