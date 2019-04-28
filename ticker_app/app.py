from datetime import datetime

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, exc

from api.app import api


app = Flask(__name__)


class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@postgres:5432/ticker_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app.config.from_object(Config)
db = SQLAlchemy(app)
app.register_blueprint(api)


@app.route('/', methods=['GET', 'POST'])
def index():
    from models import Ticker
    return render_template('index.html', tickers=Ticker.query.all())


@app.route('/<string:ticker>')
def ticker_detail(ticker):
    from models import Ticker, TickerHistory
    tick = Ticker.query.filter_by(name=ticker).options(joinedload(Ticker.history)).one_or_none()
    if not tick:
        raise exc.NoResultFound(f'ticker: {ticker} not found')

    return render_template(
        'history.html', ticker=ticker, fields=TickerHistory.fields, history=tick.history
    )


@app.route('/<ticker>/insider/<string:insider_name>')
def ticker_insider_name(ticker, insider_name):
    from models import Ticker, InsiderOperation, Insider
    ticker_id = Ticker.get_ticker(name=ticker).id
    insider = Insider.get_by_name(name=insider_name.replace('_', ' '))
    insider_operations = InsiderOperation.query.filter_by(insider_id=insider.id, ticker_id=ticker_id)

    return render_template(
        'insider_card.html', insider=insider, fields=InsiderOperation.fields, insider_operations=insider_operations
    )


@app.route('/<string:ticker>/insider')
def ticker_insider(ticker):
    from models import Ticker, Insider, InsiderOperation
    ticker_id = Ticker.get_ticker(name=ticker).id
    operations = InsiderOperation.query.filter_by(ticker_id=ticker_id)
    insiders = {}
    for operation in operations:
        if operation.insider_id in insiders:
            continue
        insiders[operation.insider_id] = Insider.query.get(operation.insider_id).name.replace(' ', '_')

    return render_template(
        'insiders.html', ticker=ticker, fields=InsiderOperation.fields, operations=operations, insiders=insiders
    )


@app.route('/<string:ticker>/analytics')
def ticker_insider_analytics(ticker):
    from models import Ticker, TickerHistory
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    rows = {}
    if all([date_from, date_to]):
        date_from = datetime.strptime(date_from, '%d-%m-%Y').date()
        date_to = datetime.strptime(date_to, '%d-%m-%Y').date()
        rows = Ticker.get_ticker(name=ticker).get_analytics(date_from, date_to)
    return render_template('analysis.html', rows=rows, fields=TickerHistory.fields, ticker=ticker)


@app.route('/<string:ticker>/delta')
def ticker_insider_delta(ticker):
    from models import Ticker
    value = request.args.get('value')
    history_type = request.args.get('type')
    result = dict.fromkeys(['date_to', 'date_from', 'delta'])
    if all([value, history_type]):
        result = Ticker.get_ticker(name=ticker).get_ticker_delta(value, history_type)

    return render_template('delta.html', ticker=ticker, result=result)


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=80)
