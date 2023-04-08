import datetime
from os import environ
import psycopg2
import requests


def date_within_range(today, val_date):
    """
    To determine if the date is within 2 weeks range
    :param today: current date
    :param val_date: date from current json item
    :return: False if the difference is more than 14 days
    """
    return (today - val_date).days < 15


class GetRawData:
    def __init__(self):
        """
        Constructor queries the api and retrieves the data
        """
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&apikey=demo'
        r = requests.get(url)
        resp_json = r.json()
        self.data = resp_json['Time Series (Daily)']

    def insert_to_db(self):
        """
        Method connects to database , parse the data initialized and inserts to the database.
        It also creates the table if not exist already.
        :return: Nothing
        """
        try:
            # Connecting to database
            conn = psycopg2.connect(environ.get('DB_URL'))
            conn.autocommit = True

            # Creating a cursor object
            cursor = conn.cursor()

            # Dropping FINANCIAL_DATA table if already exists
            # cursor.execute("DROP TABLE IF EXISTS FINANCIAL_DATA")
            with open('schema.sql', 'r') as sql_file:
                create_table = sql_file.read()
                cursor.execute(create_table)

            insert_query = """INSERT INTO financial_data (t_date, symbol, open_price, high_price,
            low_price, close_price,  volume) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            print(self.data)
            today = datetime.date.today()
            for val_date, value in self.data.items():
                if date_within_range(today, datetime.datetime.strptime(val_date, '%Y-%m-%d').date()):
                    try:
                        cursor.execute(insert_query, (val_date, 'IBM', float(value['1. open']), float(value['2. high']),
                                                      float(value['3. low']), float(value['4. close']),
                                                      int(value['6. volume'])))
                    except psycopg2.IntegrityError as err:
                        print('Similar record already exists with key ', val_date)
                else:
                    break
            conn.commit()
            print('Data exported successfully')
        except Exception:
            print('Error on connecting to db')
        finally:
            if conn:
                conn.close()
                print('Connection closed.')


if __name__ == '__main__':
    obj = GetRawData()
    obj.insert_to_db()
