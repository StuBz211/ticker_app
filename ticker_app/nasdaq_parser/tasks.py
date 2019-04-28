from nasdaq_parser import source

from models import write_operation, write_history_ticker, get_ticker


class BaseTask:
    result = None

    def run(self):
        raise NotImplemented


class TaskLoadPage(BaseTask):
    def __init__(self, ticker):
        self.ticker = ticker


class LoadPageHistorical(TaskLoadPage):
    def run(self):
        self.result = source.Client().get_historical_page(ticker=self.ticker)
        return ParseHistoricalTask(self.ticker, self.result)


class LoadPageTrade(TaskLoadPage):
    def __init__(self, ticker, page=1):
        super().__init__(ticker)
        self.page = page

    def run(self):
        self.result = source.Client().get_insider_trades(self.ticker, self.page)
        task = ParseTradeTask(self.ticker, self.result)
        task.first_load = True if self.page == 1 else False
        return task


class ParseHistoricalTask(BaseTask):
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
