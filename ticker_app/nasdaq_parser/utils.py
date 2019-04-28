import re
from datetime import datetime


def normalize_text(raw_text):
    return re.sub(r'[^\x00-\x7F]+', '', raw_text)


def sub_int(value):
    return re.sub(r',', '', value) or None


def update_dict_by_func(data, func, *args):
    for arg in args:
        data[arg] = func(data[arg])
    return data


def get_date(date_str):
    if re.match('\d\d:\d\d', date_str):
        return datetime.today().date()
    else:
        date = datetime.strptime(date_str, '%m/%d/%Y').date()
    return date
