
from urllib.parse import urljoin
import requests
import bs4


from .utils import get_date, sub_int, normalize_text, update_dict_by_func


class Client:
    BASE_URL = 'https://www.nasdaq.com'
    history_url = urljoin(BASE_URL, 'symbol/{ticker}/historical')
    trade_url = urljoin(BASE_URL, 'symbol/{ticker}/insider-trades')

    def __init__(self):
        self._req = requests.session()

    def get(self, url, page=None):
        try:
            resp = self._req.get(url, params={'page': page})
            resp.raise_for_status()
        except requests.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            return None
        return resp

    def get_historical_page(self, ticker):
        url = self.history_url.format(ticker=ticker.lower())
        resp = self.get(url)
        return resp.text

    def get_insider_trades(self, ticker, page=None):
        url = self.trade_url.format(ticker=ticker.lower())
        resp = self.get(url, page)
        return resp.text


class ParserHistorical:
    headers = ['date', 'open', 'high', 'low', 'close', 'volume']

    def __init__(self, content):
        self.content = content
        self.history_list = []

    def parse(self):
        soup = bs4.BeautifulSoup(self.content, 'lxml')
        rows = soup.select('#historicalContainer table tr')
        for row in rows[1:]:
            row_dict = {k: normalize_text(v.text.strip()) for k, v in zip(self.headers, row.select('td'))}
            if any(row_dict.values()):
                row_dict = update_dict_by_func(row_dict, sub_int, 'volume')
                row_dict = update_dict_by_func(row_dict, get_date, 'date')
                self.history_list.append(row_dict)

    def to_list(self):
        return self.history_list


class ParserTradeTicker:
    headers = [
        'insider', 'relation', 'last_date', 'transaction_type',
        'owner_type', 'shared_traded', 'last_price', 'shares_held'
    ]

    def __init__(self, content):
        self.content = content
        self.insider_trade_operations = []
        self.soup = None
        self.max_page = None

    def parse(self):
        self.soup = bs4.BeautifulSoup(self.content, 'lxml')
        self.max_page = max([int(i.text) for i in self.soup.select('#pager li') if i.text.isdigit()])
        rows = self.soup.select('.genTable table tr')

        for row in rows[1:]:
            row_dict = {k.lower(): v.text.strip() for k, v in zip(self.headers, row.select('td'))}
            row_dict['inner_id'] = row.select_one('a').attrs['href'].split('-')[-1]
            row_dict = update_dict_by_func(row_dict, sub_int, 'last_price', 'shares_held', 'shared_traded')
            row_dict = update_dict_by_func(row_dict, get_date, 'last_date')
            self.insider_trade_operations.append(row_dict)

    def to_list(self):
        return self.insider_trade_operations
