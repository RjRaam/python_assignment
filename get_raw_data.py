import datetime
from os import environ
import psycopg2
import requests

migration_interval = 14


def date_within_range(today, val_date):
    """
    To determine if the date is within migration_interval (default - 14 days).
    :param today: current date
    :param val_date: date from current json item
    :return: False if the difference is more than 14 days
    """
    return (today - val_date).days < (migration_interval + 1)


class GetRawData:
    def __init__(self):
        """
        Constructor queries the api and retrieves the data
        """
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&apikey={}'\
            .format(environ.get('API_KEY'))
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

            today = datetime.date.today()
            select_query = "SELECT count(*) from financial_data where t_date=%s"
            cursor.execute(select_query, [today])
            rows_count = cursor.fetchone()[0]
            if rows_count >= 1:
                # Avoid repeated migration for same day
                decision = input('Seems already Migration completed for today. Do you want to migrate again? Y/N')
                if decision == 'Y' or decision == 'y':
                    print('Proceeding migration')
                    pass
                else:
                    print('Migration abort.')
                    return
            insert_query = """INSERT INTO financial_data (t_date, symbol, open_price, high_price,
            low_price, close_price,  volume) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            for val_date, value in self.data.items():
                if date_within_range(today, datetime.datetime.strptime(val_date, '%Y-%m-%d').date()):
                    try:
                        cursor.execute(insert_query, (val_date, 'IBM', float(value['1. open']), float(value['2. high']),
                                                      float(value['3. low']), float(value['4. close']),
                                                      int(value['6. volume'])))
                    except psycopg2.IntegrityError as err:
                        print('Similar record already exists with key ', val_date)
                else:
                    # To terminate db insert operation for after inserting 14 days
                    break
            conn.commit()
            print('Data exported successfully')
        except psycopg2.OperationalError:
            print('Error on connecting to db')
        finally:
            if conn:
                conn.close()
                print('Connection closed.')


if __name__ == '__main__':
    obj = GetRawData()
    obj.insert_to_db()
