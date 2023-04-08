import math
from os import environ
from flask import Flask, request
import psycopg2

app = Flask(__name__)
SELECT_QUERY = """
SELECT symbol, t_date, open_price, close_price, volume FROM financial_data where t_date BETWEEN %s AND %s 
AND symbol = %s"""


def req_to_dict(req):
    """
    Method parses request param to a dict.
    Limit has default value of 5.
    limit and page are optional params.
    :param req: api request
    :return: request parsed to dict
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    symbol = request.args.get('symbol')
    # default limit is 5
    limit = 5 if request.args.get('limit') is None else int(request.args.get('limit'))
    page = 1 if request.args.get('page') is None else int(request.args.get('page'))
    return {'start_date': start_date, 'end_date': end_date, 'symbol': symbol, 'limit': limit, 'page': page}


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
    cursor.execute(SELECT_QUERY, (req_dict.get('start_date'), req_dict.get('end_date'), req_dict.get('symbol')))
    return cursor.fetchall()


@app.route('/api/financial_data', methods=['GET'])
def financial_data():
    """
    Method parses req params and queries db based on the parsed params.
    It also calculates pagination and validates param type, incorrect values and mandatory param check.
    :return: json resp in the requirement format.
    """
    data = []
    # Parsing request parameters to a dictionary
    req_dict = req_to_dict(request)
    records = fetch_records(req_dict)
    count = len(records)
    limit = req_dict.get('limit')
    page = req_dict.get('page')
    pages = math.ceil(count / 5) if page is None else math.ceil(count / limit)
    items_to_skip = None if page is 1 else (page - 1) * limit
    items_to_display = limit if page is 1 else ((page - 1) * limit) + limit
    for record in records[items_to_skip:items_to_display]:
        db_dict = {'symbol': record[0], 'date': record[1], 'open_price': record[2], 'close_price': record[3],
                   'volume': record[4]}
        data.append(db_dict)
    pagination = {'count': count, 'page': page, 'limit': limit, 'pages': pages}
    return {'data': data, 'pagination': pagination}


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
    req_dict = req_to_dict(request)
    records = fetch_records(req_dict)
    count = len(records)
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
    info = {'error': ''}
    return {'data': data, 'info': info}


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
