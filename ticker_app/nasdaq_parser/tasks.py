"""Моудль задач:
 - получения контента
 - парсинг
 - запись данные в базу данных
"""
import abc

from models import write_operation, write_history_ticker, get_ticker


from nasdaq_parser import source


class BaseTask(abc.ABC):
    result = None

    def run(self):
        raise NotImplemented


class TaskLoadPageTask(BaseTask):
    def __init__(self, ticker):
        self.ticker = ticker


class LoadPageHistoricalTask(TaskLoadPageTask):
    """задача на получение страницы с котировками на 3 месяца по названию акции"""
    def run(self):
        self.result = source.Client().get_historical_page(ticker=self.ticker)
        return ParseHistoricalTask(self.ticker, self.result)


class LoadPageTradeTask(TaskLoadPageTask):
    """задача на получение данных по операции с акциями"""
    def __init__(self, ticker, page=1):
        super().__init__(ticker)
        self.page = page

    def run(self):
        self.result = source.Client().get_insider_trades(self.ticker, self.page)
        task = ParseTradeTask(self.ticker, self.result)
        task.first_load = True if self.page == 1 else False
        return task


class ParseHistoricalTask(BaseTask):
    """задача на парсинг сведений по котировкам акции"""
    def __init__(self, ticker, content):
        self.content = content
        self.ticker = ticker

    def run(self):
        parser = source.ParserHistorical(self.content)
        parser.parse()

        ticker = get_ticker(self.ticker)
        for data in parser.to_list():
            write_history_ticker(ticker.id, data)


class ParseTradeTask(BaseTask):
    """задача на парсинг операций по акции"""
    def __init__(self, ticker, content):
        self.ticker = ticker
        self.content = content
        self.max_page = self.first_load = None

    def run(self):
        parser = source.ParserTradeTicker(self.content)
        parser.parse()

        self.max_page = parser.max_page
        for data in parser.to_list():
            write_operation(self.ticker, data)
