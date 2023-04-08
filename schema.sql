CREATE TABLE IF NOT EXISTS financial_data
(
    t_date date NOT NULL,
    symbol character varying(15) NOT NULL,
    open_price real NOT NULL,
    close_price real NOT NULL,
    high_price real NOT NULL,
    low_price real NOT NULL,
    volume bigint NOT NULL,
    CONSTRAINT financial_data_pkey PRIMARY KEY (t_date)
)