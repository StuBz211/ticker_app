"""Модуль для работа с потоками и задачами"""
import time
import queue
from threading import Thread

from nasdaq_parser import tasks


class Worker(Thread):
    def __init__(self, task_queue):
        super().__init__()
        self.tasks = task_queue
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                task = self.tasks.get()
                next_task = task.run()

                # Если задача на парсинг первой страницы оргов владельцев,
                # то добавим в задачи на загрузку, по количеству страниц
                if isinstance(task, tasks.ParseTradeTask) and task.first_load:
                    max_page = task.max_page + 1
                    max_page = max_page if max_page < 11 else 11
                    for page_num in range(2, max_page):
                        self.tasks.put(tasks.LoadPageTrade(task.ticker, page_num))

                if next_task:
                    self.tasks.put(next_task)

            finally:
                self.tasks.task_done()


class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = queue.Queue()
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, task):
        self.tasks.put(task)

    def wait_completion(self):
        self.tasks.join()


def run_parse(tickers, n=1):
    """запустим парсинг

    args:
        tickers: список названий акций
        n: количество воркеров
    """
    print('start parse')
    print('tickers count:', len(tickers))
    print('workers count:', n)

    pool = ThreadPool(int(n))
    start_time = time.time()
    for ticker in tickers:
        pool.add_task(tasks.LoadPageHistorical(ticker))
        pool.add_task(tasks.LoadPageTrade(ticker))

    pool.wait_completion()
    print('parsing done')
    print('work time:', time.time() - start_time)


if __name__ == '__main__':
    # run test
    run_parse(['CVX', 'AAPL', 'GOOG'], 3)
