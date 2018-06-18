import pytz
import datetime
import time
import decimal
import locale
import urllib
import json

import dateutil.parser

import utils.time
from urllib import urlencode


locale.setlocale(locale.LC_ALL, '')


def paramify(url, **kwargs):
    """
        Sticks the kwargs into the url as parameters.
        INPUT
            url: www.google.com, kwargs: {'go':[1,2], 'do':2}
        OUTPUT
            "www.google.com?go=1&go=2&do=2"

    """
    return "{0}?{1}".format(url, urlencode(kwargs, doseq=1)) if kwargs else url


def to_json(string):
    return json.dumps(string, sort_keys=True, indent=4, separators=(',', ': '))


def to_mapping(string):
    return json.loads(string)


def until(dt):
    current_time = datetime.datetime.now(pytz.UTC)
    remaining = dt - current_time

    # TODO: upgrade to 2.7 so we dont have to math ourselves?
    total_seconds = (remaining.microseconds + (
        remaining.seconds + remaining.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    hrs_remaining = total_seconds / 3600
    min_remaining = total_seconds % 3600 / 60
    secs_remaining = (total_seconds - hrs_remaining * 3600 - min_remaining * 60)

    market_closes_in = ''
    if hrs_remaining > 0:
        market_closes_in = '{0} hrs'.format(hrs_remaining)
    if min_remaining > 0:
        market_closes_in += ' {0} min'.format(min_remaining)
    if secs_remaining > 0:
        market_closes_in += ' {0} sec'.format(secs_remaining)
    return market_closes_in


def timestamp(dt):
    if isinstance(dt, basestring):
        dt = dateutil.parser.parse(dt)
    return time.mktime(dt.timetuple())


def datetimeformat(value, format=None):
    if not value:
        return None

    if not isinstance(value, datetime.datetime):
        parsed = dateutil.parser.parse(value)
    else:
        parsed = value
    if not format:
        return utils.time.get_full_datetime(parsed)
    else:
        return utils.time.get_full_datetime(parsed, format)


def dateformat(value, format='%m/%d/%Y'):
    if not value:
        return None

    if not isinstance(value, datetime.datetime) and \
            not isinstance(value, datetime.date):
        parsed = dateutil.parser.parse(value)
    else:
        parsed = value
    return utils.time.get_date(parsed, format)


def timeformat(value, format='%I:%M %P %Z'):
    if not value:
        return None

    if not isinstance(value, datetime.datetime):
        parsed = dateutil.parser.parse(value)
    else:
        parsed = value
    return utils.time.get_time(parsed, format)


def prettytime(value):
    if not value:
        return None
    if isinstance(value, float):
        value = datetime.datetime.fromtimestamp(value).isoformat()
    parsed = dateutil.parser.parse(value)
    now = datetime.datetime.now(parsed.tzinfo)
    diff = now - parsed

    # Have to check days first due to the way time delta's work in regards to seconds
    if diff.days > 0:
        return '{0} days ago'.format(diff.days)
    else:
        if diff.seconds < 3600:
            return '{0} minutes ago'.format(diff.seconds / 60)
        elif diff.seconds < 7200:
            return '1 hour and {0} minutes ago'.format((diff.seconds - 3600) / 60)
        elif diff.seconds < 86400:
            return '{0} hours ago'.format(diff.seconds / 3600)

    return


def phoneformat(s):
    if not isinstance(s, basestring):
        s = str(s)
    return '({0}) {1}-{2}'.format(s[:3], s[3:6], s[6:10])

def titlesecurity(s):
    if not s:
        return s
    if not isinstance(s, basestring):
        s = str(s)
    a = s.split()
    l = []
    for i in a:
        if len(i) <= 2:
            l.append(i.upper())
        else:
            l.append(i.capitalize())
    return " ".join(l)


def urlencode_filter(s):
    return urllib.quote_plus(str(s.encode("utf-8")))


def dec_filter(f):
    return decimal.Decimal(str(f))


def percent_filter(f):
    return '{0}%'.format(decimal.Decimal(str(f * 100)))


def currency_filter(amount):
    return locale.currency(float(amount), grouping=True)


def frac_currency_filter(amount):
    formatted = locale.format('%.4f', decimal.Decimal(amount),
                              grouping=True, monetary=True)
    return formatted[:-2] if formatted.endswith('00') else formatted


def floatformat_filter(value):
    return locale.format("%.2f", value, grouping=True)


def intformat_filter(value):
    return locale.format("%d", value, grouping=True)


def numformat_filter(value):
    filters = {
        float: floatformat_filter,
        int: intformat_filter,
        decimal.Decimal: floatformat_filter
    }
    return filters[type(value)](value)


def mask_filter(s, sub='x', show_last=None):
    """
        "Hides" chars in a string. Defaults to masking the entire string.
    :param s: string to mask
    :param sub: char to mask with
    :param show_last: (int) reveals the last n chars
    :return: hidden string

    example:
       {{ ssn }}
       {{ ssn | mask }}
       {{ ssn | mask(show_last=4) }}
    prints:
       123121234
       xxxxxxxxx
       xxxxx1234
    """
    # default: mask the whole thing
    result = sub * len(s)
    if show_last is not None:
        mask = max(len(s) - show_last, 0)
        result = ''.join([sub * mask, s[mask:]])
    return result


def insert_filter(s, indices, sep='-'):
    """
        Separates a string with sep char
    :param s: string to separate
    :param indices: list of int index locations to insert the char
    :param sep: char to insert
    :return: separated string

    example:
        {{ ssn }}
        {{ ssn | insert([3,5]) }}
    prints:
       123121234
       123-12-1234
    """
    parts = [s[i:j] for i, j in zip([0]+indices, indices+[None])]
    return sep.join(parts)


def url_args_filter(params, ignore_keys=None):
    """
        unwraps params as url args
    """
    data = params
    if ignore_keys:
        data = dict((k, params[k]) for k in params.iterkeys()
                    if k not in ignore_keys)
    return paramify('', **data)


def shortnumformat(value):
    if value < 1000:
        return locale.format("%.1f", value)
    elif value >= 1000 and value < 1000000:
        return ''.join([locale.format("%.1f", value/decimal.Decimal('1000')),'K'])
    elif value >= 1000000 and value < 1000000000:
        return ''.join([locale.format("%.1f", value/decimal.Decimal('1000000')),'M'])
    else:
        return ''.join([locale.format("%.1f", value/decimal.Decimal('1000000000')),'B'])


def millionformat(value):
    return ''.join([locale.format("%.1f", decimal.Decimal(str(value))/decimal.Decimal('1000000')),'M'])


def to_dict(cls):
    """
        Converts a const class to a dict. Useful for piping into dictsort.
    :param cls: a class object with only named values (ex AccountAppStatus)
    :return: a dict representation of this object.
    """
    return dict((name, getattr(cls, name)) for name in dir(cls)
                if not name.startswith('__'))
