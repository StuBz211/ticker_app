"""Моудль моделей БД"""
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.sql import text
from sqlalchemy import and_

from app import db


class Ticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, index=True, unique=True)
    history = db.relationship('TickerHistory', backref='ticker')

    def __repr__(self):
        return f'{self.__class__}({self.id}, {self.name})'

    def to_dict(self):
        return {'id': self.id, 'name': self.name}

    @classmethod
    def get_ticker(cls, name):
        return cls.query.filter_by(name=name).one()

    def get_ticker_delta(self, value, history_type):
        result = {}
        if history_type in TickerHistory.__dict__:
            raw_sql = text(
                """
                WITH lo as (
                    SELECT date, open, low, high, close
                    FROM ticker_history
                    WHERE ticker_id = :ticker_id AND date = (SELECT min(date) FROM ticker_history WHERE ticker_id =:ticker_id)
                )
                SELECT
                    lo.date as lo_date, th.date as hi_date, th.open - lo.open
                from ticker_history as th, lo
                WHERE ticker_id = :ticker_id AND th.""" + history_type + ' - lo. ' + history_type + """> :value
                    ORDER BY th.date
                    LIMIT 1
                    """
            )
            value = float(value)
            fetch = db.session.execute(
                raw_sql,
                {'value': value, 'ticker_id': self.id}
            ).fetchone()
            if fetch:
                date_from, date_to, delta = fetch
                result['date_to'] = str(date_to)
                result['date_from'] = str(date_from)
                result['delta'] = round(delta, 2)
        return result

    def get_analytics(self, date_from, date_to):
        rows = {}
        lohi = TickerHistory.query.filter_by(ticker_id=self.id).filter(
            and_(TickerHistory.date >= date_from, TickerHistory.date <= date_to)
        ).all()
        if lohi:
            lo, hi = min(lohi, key=lambda x: x.date), max(lohi, key=lambda x: x.date)

            analysis = {}
            for field in TickerHistory.fields:
                analysis[field] = round(getattr(hi, field) - getattr(lo, field), 2)
            rows = {'hi': hi.to_dict(), 'analytics': analysis, 'lo': lo.to_dict()}
        return rows


class TickerHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker_id = db.Column(db.Integer, db.ForeignKey('ticker.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Float)
    high = db.Column(db.Float)
    low = db.Column(db.Float)
    close = db.Column(db.Float)
    volume = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint('ticker_id', 'date', name='ticker_history_unique'),
    )

    fields = ['open', 'high', 'low', 'close']

    def to_dict(self):
        return {
            'id': self.id,
            'ticker_id': self.ticker_id,
            'date': str(self.date),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

    def __repr__(self):
        return f'{self.__class__}({self.ticker_id}, {self.date})'


class Insider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inner_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False, index=True)
    operations = db.relationship('InsiderOperation', backref='insider')
    tickers = db.relationship('Ticker', secondary='ticker_owner', backref=db.backref('ticker_owners', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('inner_id', 'name', name='insider_unique'),
    )

    def __repr__(self):
        return f'{self.__class__}({self.id}, {self.name})'

    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).one()

    def to_dict(self):
        return {
            'id': self.id,
            'inner_id': self.inner_id,
            'name': self.name,
            'operations': [i.to_dict() for i in self.operations],
            'tickers': [i.to_dict() for i in self.tickers]
        }


class InsiderOperation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insider_id = db.Column(db.Integer, db.ForeignKey('insider.id'), nullable=False, index=True)
    ticker_id = db.Column(db.Integer, db.ForeignKey('ticker.id'), nullable=False, index=True)
    relation = db.Column(db.String)
    last_date = db.Column(db.Date)
    transaction_type = db.Column(db.String)
    owner_type = db.Column(db.String)
    shared_traded = db.Column(db.Integer)
    last_price = db.Column(db.Float)
    shares_held = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint(
            'insider_id', 'ticker_id', 'last_date', 'relation', 'transaction_type', 'owner_type', 'shared_traded',
            name='insider_operations_unique'
        ),
    )

    fields = ['relation', 'last_date', 'transaction_type', 'owner_type', 'shared_traded', 'last_price', 'shares_held']

    def __repr__(self):
        return f'{self.__class__}({self.id}, {self.insider_id}, {self.ticker_id},{self.last_date})'

    def to_dict(self):
        return {
            'id': self.id,
            'insider_id': self.insider_id,
            'ticker_id': self.ticker_id,
            'relation': self.relation,
            'last_date': str(self.last_date),
            'transaction_type': self.transaction_type,
            'owner_type': self.owner_type,
            'shared_traded': self.shared_traded,
            'last_price': self.last_price,
            'shares_held': self.shares_held
        }


db.Table(
    'ticker_owner',
    db.Column('ticker_id', db.Integer, db.ForeignKey('ticker.id')),
    db.Column('insider_id', db.Integer, db.ForeignKey('insider.id'))
)


def except_decorator(*exceptions):
    """Декоратор отлавливает ошибки, которые переданы в аргементе"""
    def wrapper(func):
        def execute(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                pass

        return execute

    return wrapper


def get_or_create(session, model, defaults=None, **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), False
    except InvalidRequestError:
        session.rollback()
        if defaults is not None:
            kwargs.update(defaults)
        try:
            with session.begin_nested():
                instance = model(**kwargs)
                session.add(instance)
                return instance, True
        except IntegrityError:
            return session.query(model).filter_by(**kwargs).one(), False


def get_ticker(ticker_name):
    ticker, created = get_or_create(db.session, Ticker, name=ticker_name)
    return ticker


def get_insider(name, inner_id):
    insider, created = get_or_create(db.session, Insider, name=name, inner_id=inner_id)
    return insider


@except_decorator(IntegrityError, InvalidRequestError)
def write_history_ticker(ticker_id, data):
    th = TickerHistory(
        ticker_id=ticker_id,
        **data
    )
    db.session.add(th)
    db.session.commit()


@except_decorator(InvalidRequestError, IntegrityError)
def write_operation(ticker_name, data):
    insider = get_insider(name=data.pop('insider'), inner_id=data.pop('inner_id'))
    ticker = get_ticker(ticker_name)
    ticker.ticker_owners.append(insider)
    ins_op = InsiderOperation(
        insider_id=insider.id,
        ticker_id=ticker.id,
        **data
    )
    db.session.add(ins_op)
    db.session.commit()
