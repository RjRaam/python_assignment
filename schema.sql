CREATE TABLE IF NOT EXISTS financial_data
(
    t_date date,
    symbol character varying(15),
    open_price real NOT NULL,
    close_price real NOT NULL,
    high_price real NOT NULL,
    low_price real NOT NULL,
    volume bigint NOT NULL,
    CONSTRAINT financial_data_key PRIMARY KEY (t_date, symbol)
)