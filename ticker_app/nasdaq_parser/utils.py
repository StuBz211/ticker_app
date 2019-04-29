"""Утилиты"""
import re
from datetime import datetime


def normalize_text(raw_text):
    """удалить из текста ascii символы"""
    return re.sub(r'[^\x00-\x7F]+', '', raw_text)


def sub_int(value):
    """удалить запятые из значения"""
    return re.sub(r',', '', value) or None


def update_dict_by_func(data, func, *args):
    """обновить словарь функцией у ключей переданных в функции"""
    for arg in args:
        if arg not in data:
            continue
        data[arg] = func(data[arg])
    return data


def get_date(date_str):
    """Получить дату из строки"""
    # случай отображения сегодняшней даты.
    if re.match('\d\d:\d\d', date_str):
        return datetime.today().date()
    else:
        date = datetime.strptime(date_str, '%m/%d/%Y').date()
    return date
