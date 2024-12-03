import requests
import math
import json
import pandas as pd
import calendar
import datetime

lookback_in_months = 12
nifty_json_data = "nifty.json"


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def download_latest_nifty_data():
    end_date = datetime.date.today()
    end_date_unix = datetime.datetime.combine(
        end_date, datetime.datetime.min.time()
    ).timestamp()
    start_date = add_months(end_date, -lookback_in_months)
    start_date_unix = datetime.datetime.combine(
        start_date, datetime.datetime.min.time()
    ).timestamp()
    url = r"https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?events=capitalGain%7Cdiv%7Csplit&formatted=true&includeAdjustedClose=true&interval=1d&period1={{start_date}}&period2={{end_date}}&symbol=%5ENSEI&userYfid=true&lang=en-US&region=US"

    url = url.replace(r"{{start_date}}", str(int(start_date_unix)))
    url = url.replace(r"{{end_date}}", str(int(end_date_unix)))

    # response = requests.get(url)
    # print(response.content)


def parse_nifty_data_to_dataframe():
    with open("nifty_json_data.json", "r") as f:
        data = json.loads(f.read())
    # print(data)
    df = pd.DataFrame()
    df["unixtimestamp"] = data["chart"]["result"][0]["timestamp"]
    df["date"] = df["unixtimestamp"].apply(
        lambda x: datetime.datetime.fromtimestamp((x))
    )
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["high"] = data["chart"]["result"][0]["indicators"]["quote"][0]["high"]
    df["low"] = data["chart"]["result"][0]["indicators"]["quote"][0]["low"]
    df["close"] = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    # df["expiry"] = "N"
    # print(df.head())
    return df


def get_next_or_same_thursday(input_date):
    days_ahead = 3 - input_date.weekday()  # Thursday is 3
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return input_date + datetime.timedelta(days=days_ahead)


def add_first_close_price(df):
    # Create a new column with first close price for each expiry group
    first_close = df.groupby("expirydate")["close"].transform("first")
    first_close_date = df.groupby("expirydate")["date"].transform("first")
    df["firstclose"] = first_close
    df["firstclosedate"] = first_close_date
    return df


def conditional_round_100(x):
    remainder = x % 100
    if remainder >= 50:
        return math.ceil(x / 100) * 100
    return math.floor(x / 100) * 100


def select_expiry_dates(df):
    df["thursdays"] = df["date"].apply(lambda x: get_next_or_same_thursday(x))

    # Create a series of all unique dates and thursdays
    all_dates = pd.Series(df["date"].unique()).sort_values()
    thursdays = pd.Series(df["thursdays"].unique())

    # Create a mapping series
    date_mapping = pd.Series(index=thursdays)

    for thursday in thursdays:
        # Find the closest previous date that exists
        mask = all_dates <= thursday
        if mask.any():
            date_mapping[thursday] = all_dates[mask].max()
        else:
            date_mapping[thursday] = None

    # Map the dates back to the original dataframe
    df["expirydate"] = df["thursdays"].map(date_mapping)

    df["expirydate"] = df["expirydate"].apply(lambda x: x.date())
    df["thursdays"] = df["thursdays"].apply(lambda x: x.date())

    df = add_first_close_price(df)
    df["strikeprice"] = df["firstclose"].apply(conditional_round_100)

    return df


if __name__ == "__main__":
    # download_latest_nifty_data()
    df = parse_nifty_data_to_dataframe()
    df = select_expiry_dates(df)

    print(df.head())
    df.to_csv("data.csv", header=True, index=False)
