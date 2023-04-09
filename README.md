# Financial Data retrieval and statistics
## Introduction
This project helps retrieve the financial data of the stocks (IBM, Apple Inc.)for the last two weeks from the API AlphaVantage (https://www.alphavantage.co)

## Features
Any user with a valid API Key from AlphaVantage can use this API.

## Data Migration
### Local Environment
      From Pycharm IDE:
         1. Edit Configurations -> Add New python configuration -> Choose "get_raw_data.py" for "Script path".
         2. Working Directory -> root directory (python_assignment).
         3. Add environment variable "DB_URL=postgres://{db_username}:{db_password}@localhost:{db_port}/{db_name};API_KEY={api_key}" to run_configuration. (replace values accordingly)
         4. Python Interpreter -> 3.8 (Preferred) or above.
### From cmd/terminal
      1. Add the following system environment variables(replace values accordingly)
         1. "DB_URL" with the value "postgres://{db_username}:{db_password}@localhost:{db_port}/{db_name}"
         2.. "API_KEY" with the value "{api_key}"
      2. Move to the root directory (python_assignment).
      3. Run the command "python get_raw_data.py".
### From Docker
      Run the docker container before executing following steps.
      1. Move to root directory (python_assignment).
      2. Run the command "python get_raw_data.py".

## Starting the API
### Prerequisites
Complete Data Migration steps as mentioned above.
#### From Pycharm IDE:
      1. Edit Configurations -> Add New python configuration -> Choose "financial/app.py" for "Script path".
      2. Working Directory -> root directory (python_assignment).
      3. Add environment variable "DB_URL=postgres://{db_username}:{db_password}@localhost:{db_port}/{db_name};API_KEY={api_key}" to run_configuration. (replace values accordingly)
      4. Python Interpreter -> 3.8 (Preferred) or above.
#### From cmd/terminal
      1. Move to the root directory (python_assignment).
      2. Run the command "flask --app app --debug run".
#### From Docker
##### Using environment file
      Prepare a file named '.env' in the root directory with all the environment variables and execute the below command
         "docker-compose --env-file .env up -d"

      Passing environment variables from CLI:
         "docker run -d -t -i -e POSTGRES_USER={db_username}-e POSTGRES_PASSWORD:{db_password>} -e POSTGRES_DB:{db_name} up -d"

## API Endpoints
| Method | Endpoints                                          | Action                                                           |
|--------|----------------------------------------------------|------------------------------------------------------------------|
| GET    | `/api/financial_data/:start_date&:end_date&symbol` | To retrieve financial data that satisfies the request params     |
| GET    | `/api/statistics/:start_date&:end_date&symbol`     | To retrieve financial statistics that satisfies the request params |

#### Note
      'finanical_data' endpoint will support optional params `limit` <no of data per page> and `page` <page navigation>
## Status Codes

API returns the following status codes :

| Status Code | Status                  | Description                                                     |
| :--- |:------------------------|:----------------------------------------------------------------|
| 200 | `OK`                    | On successful data retrieval                                    |
| 400 | `BAD REQUEST`           | Mandatory Param missing or invalid param value                  |
| 404 | `NOT FOUND`             | No data retrieved  or Table not found (Migration not performed) |

## Libraries Used
      1. Flask api used for the api support. Used Flask as it is a Microframework and lightweight.
      2. psycopg2 - adapter to connect and work with PostgreSQL.
      3. requests - to handle Http requests