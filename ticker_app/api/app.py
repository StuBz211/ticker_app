"""Модуль для работы для выдачи запросов в формате json"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import and_
from sqlalchemy.sql import text


api = Blueprint('api', __name__, url_prefix='/api')


@api.route("/")
def index():
    from models import Ticker
    return jsonify({'tickers': [i.to_dict() for i in Ticker.query.all()]})


@api.route('/<string:ticker>')
def ticker_detail(ticker):
    from models import Ticker
    history = Ticker.get_ticker(name=ticker).history
    fields = ['date', 'open', 'high', 'low', 'volume']
    return jsonify({'ticker': ticker, 'fields': fields, 'history': [i.to_dict() for i in history]})


@api.route('/<ticker>/insider/<string:insider_name>')
def ticker_insider_name(ticker, insider_name):
    from models import Insider
    insider = Insider.get_by_name(name=insider_name.replace('_', ' '))
    fields = ['relation', 'last_date', 'transaction_type',
              'owner_type', 'shared_traded', 'last_price', 'shares_held']
    insider_dict = insider.to_dict()
    return jsonify(dict(insider=insider_dict, fields=fields))


@api.route('/<string:ticker>/insider')
def ticker_insider(ticker):
    from models import Ticker, Insider, InsiderOperation
    ticker_id = Ticker.get_ticker(name=ticker).id
    operations = InsiderOperation.query.filter_by(ticker_id=ticker_id)

    insiders = {}
    for operation in operations:
        if operation.insider_id in insiders:
            continue
        insiders[operation.insider_id] = Insider.query.get(operation.insider_id).name.replace(' ', '_')
    operations = [operation.to_dict() for operation in operations]
    return jsonify(dict(ticker=ticker, fields=fields, operations=operations, insiders=insiders))


@api.route('/<string:ticker>/analytics')
def ticker_insider_analytics(ticker):
    from models import Ticker, TickerHistory
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if all([date_from, date_to]):
        date_from = datetime.strptime(date_from, '%d-%m-%Y').date()
        date_to = datetime.strptime(date_to, '%d-%m-%Y').date()
        rows = Ticker.get_ticker(name=ticker).get_analytics(date_from, date_to)
        return jsonify({'rows': rows, 'fields': TickerHistory.fields, 'ticker': ticker})


@api.route('/<string:ticker>/delta')
def ticker_insider_delta(ticker):
    from models import Ticker
    value = request.args.get('value')
    history_type = request.args.get('type')
    result = dict.fromkeys(['date_to', 'date_from', 'delta'])
    if all([value, history_type]):
        result = Ticker.get_ticker(name=ticker).get_ticker_delta(value, history_type)
    return jsonify({'ticker': ticker, 'delta': result})
