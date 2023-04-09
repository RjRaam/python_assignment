import math
from datetime import datetime
from os import environ
from flask import Flask, request
import psycopg2
from requests import HTTPError
import json

app = Flask(__name__)
SELECT_QUERY = """
SELECT symbol, t_date, open_price, close_price, volume FROM financial_data where t_date BETWEEN %s AND %s 
AND symbol = %s"""
SUCCESS_STATUS_CODE = 200
MANDATORY_PARAMS = ('start_date', 'end_date', 'symbol')


class NoDataFoundError(HTTPError):
    """
    Thrown when there is no data returned from database for the request params
    """
    status_code = 404
    message = {'error': 'Oops! No data found'}


class MandatoryParamError(HTTPError):
    """
    Thrown when any or all the mandatory params missing in the request
    """
    status_code = 400
    message = {'error': 'Missing mandatory param(s) - {start_date, end_date and symbol}'}


class InvalidRequestError(HTTPError):
    """
    Thrown when invalid value given in the request param
    """
    status_code = 400
    message = {'error': 'Invalid request'}


class TableNotFoundError(HTTPError):
    """
    Thrown when table not found(Migration not done before hitting endpoints)
    """
    status_code = 404
    message = {'error': 'Table not found! Is the data migration completed?!'}


class DateParamError(HTTPError):
    """
    Thrown when start_date is greater than end_date in request param
    """
    status_code = 400
    message = {'error': 'start_date cannot be greater than end_date!'}


def resp_obj(status_code, message):
    return json.dumps({'data': {}, 'pagination': {}, 'info': message}, default=lambda o: o.__dict__, indent=4), \
        status_code


@app.errorhandler(NoDataFoundError)
def handle_exception(err):
    return resp_obj(err.status_code, err.message)


@app.errorhandler(MandatoryParamError)
def handle_exception(err):
    return resp_obj(err.status_code, err.message)


@app.errorhandler(TableNotFoundError)
def handle_exception(err):
    return resp_obj(err.status_code, err.message)


@app.errorhandler(InvalidRequestError)
def handle_exception(err):
    return resp_obj(err.status_code, err.message)


@app.errorhandler(DateParamError)
def handle_exception(err):
    return resp_obj(err.status_code, err.message)


def is_mandatory_params_exist(req):
    if len(req.args) < 3:
        return False
    else:
        for param in MANDATORY_PARAMS:
            if req.args.get(param) is None:
                return False
    return True


def req_to_dict(req):
    """
    Method parses request param to a dict.
    Limit has default value of 5.
    limit and page are optional params.
    :param req: api request
    :return: request parsed to dict
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        symbol = request.args.get('symbol')
        if is_mandatory_params_exist(request):
            if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                raise DateParamError
            # default limit is 5
            limit = 5 if request.args.get('limit') is None else int(request.args.get('limit'))
            page = 1 if request.args.get('page') is None else int(request.args.get('page'))

            if limit == 0 or page == 0:
                raise InvalidRequestError

            return {'start_date': start_date, 'end_date': end_date, 'symbol': symbol, 'limit': limit, 'page': page}
        else:
            raise MandatoryParamError
    except ValueError:
        raise InvalidRequestError


def fetch_records(req_dict):
    """
    Queries db based on the dict argument value.
    Records between the start and end date that has the symbol in request will be retrieved.
    :param req_dict: Parsed req params
    :return: records retrieved from database
    """
    # Connecting to database
    conn = psycopg2.connect(environ.get('DB_URL'))
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    try:
        cursor.execute(SELECT_QUERY, (req_dict.get('start_date'), req_dict.get('end_date'), req_dict.get('symbol')))
        return cursor.fetchall()
    except psycopg2.errors.InvalidDatetimeFormat:
        raise InvalidRequestError
    except psycopg2.errors.UndefinedTable:
        raise TableNotFoundError


def to_str_date(sql_date):
    return sql_date.strftime("%Y-%m-%d")


@app.route('/api/financial_data', methods=['GET'])
def financial_data():
    """
    Method parses req params and queries db based on the parsed params.
    It also calculates pagination and validates param type, incorrect values and mandatory param check.
    :return: json resp in the requirement format.
    """
    data = []
    info = {'error': {}}
    # Parsing request parameters to a dictionary
    req_dict = req_to_dict(request)
    records = fetch_records(req_dict)
    count = len(records)

    if count < 1:
        raise NoDataFoundError

    limit = req_dict.get('limit')
    if limit > count:
        limit = count
        info['error'] = 'limit reset to max record retrieved from database.'

    page = req_dict.get('page')
    pages = math.ceil(count / 5) if page is None else math.ceil(count / limit)
    if page > pages:
        page = pages
        info['error'] = 'page not exist! Reset to last page'
    items_to_skip = None if page == 1 else (page - 1) * limit
    items_to_display = limit if page == 1 else ((page - 1) * limit) + limit
    for record in records[items_to_skip:items_to_display]:
        db_dict = {'symbol': record[0], 'date': to_str_date(record[1]), 'open_price': record[2],
                   'close_price': record[3],
                   'volume': record[4]}
        data.append(db_dict)
    pagination = {'count': count, 'page': page, 'limit': limit, 'pages': pages}
    return json.dumps({'data': data, 'pagination': pagination, 'info': info}, default=lambda o: o.__dict__, indent=4), \
        SUCCESS_STATUS_CODE


@app.route('/api/statistics')
def statistics():
    """
    Method parses req params and queries db based on the parsed params.
    It returns data statistics based on the query result.
    It also validates param type, incorrect values and mandatory params.
    :return: avg values based on the parsed
    """
    # Parsing request parameters to a dictionary
    data = {}
    info = {'error': ''}
    req_dict = req_to_dict(request)
    records = fetch_records(req_dict)
    count = len(records)

    if count < 1:
        raise NoDataFoundError

    total_open_price = 0
    total_close_price = 0
    total_volume = 0
    for result in records:
        total_open_price += result[2]
        total_close_price += result[3]
        total_volume += result[4]
    data['start_date'] = req_dict.get('start_date')
    data['end_date'] = req_dict.get('end_date')
    data['symbol'] = req_dict.get('symbol')
    data['average_daily_open_price'] = total_open_price / count
    data['average_daily_close_price'] = total_close_price / count
    data['average_daily_volume'] = total_volume / count
    return json.dumps({'data': data, 'info': info}, default=lambda o: o.__dict__, indent=4), SUCCESS_STATUS_CODE
