from flask_script import Manager

from app import app, db


manager = Manager(app)


@manager.command
def init_db():
    import models
    db.create_all()
    db.session.commit()


@manager.command
def parse(workers=2):
    from nasdaq_parser import run_parse
    with open('tickers.txt') as f:
        tickets = [i.strip() for i in f.readlines()]
        run_parse(tickets, workers)



if __name__ == '__main__':
    manager.run()
