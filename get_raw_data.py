from datetime import datetime, date, timedelta
from os import environ
import psycopg2
import requests

# Dict key - Symbol to query the AlphaVantage Api , Value - Related company name
SYMBOLS = {'IBM': 'IBM', '0R2V.LON': 'Apple Inc.'}
MIGRATION_INTERVAL = 14
SELECT_QUERY = "SELECT count(*) from financial_data where t_date=%s and symbol=%s"
INSERT_QUERY = """INSERT INTO financial_data (t_date, symbol, open_price, high_price,
low_price, close_price, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)"""


def date_within_range(today, val_date):
    """
    To determine if the date is within migration_interval (default - 14 days).
    :param today: current date
    :param val_date: date from current json item
    :return: False if the difference is more than 14 days
    """
    return (today - val_date).days < (MIGRATION_INTERVAL + 1)


def get_current_date():
    """
    If today is a weekend, return last friday as current date since stock api only has weekdays
    :return: today's date/last friday's date (if today is weekend)
    """
    today = date.today()
    if today.weekday() > 4:
        offset = (today.weekday() - 4) % 7
        return today - timedelta(days=offset)
    else:
        return date.today()


class GetRawData:
    def __init__(self):
        """
        Constructor queries the api and retrieves the data
        """
        # Dictionary key - company name, value - Stock data retrieved from Api call
        self.data = {}
        for symbol, company_name in SYMBOLS.items():
            # Loop through the companies dictionary to get Stock data
            url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={}&apikey={}' \
                .format(symbol, environ.get('API_KEY'))
            r = requests.get(url)
            resp_json = r.json()
            self.data[company_name] = resp_json['Time Series (Daily)']

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

            today = get_current_date()
            for company_name, resp_data in self.data.items():
                cursor.execute(SELECT_QUERY, [today, company_name])
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

                for report_date, value in resp_data.items():
                    if date_within_range(today, datetime.strptime(report_date, '%Y-%m-%d').date()):
                        try:
                            cursor.execute(INSERT_QUERY,
                                           (report_date, company_name, float(value['1. open']), float(value['2. high']),
                                            float(value['3. low']), float(value['4. close']), int(value['6. volume'])))
                        except psycopg2.IntegrityError as err:
                            print('Similar record already exists with key ', report_date)
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
