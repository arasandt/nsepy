import os
import requests
import math
import json
import time
import pandas as pd
import calendar
import datetime
import zipfile
import io
from fake_useragent import UserAgent

# from nsepy import get_history
from urllib.parse import quote, urlencode, quote_plus

lookback_in_months = 12
nifty_json_data = "nifty.json"

fo_dir = "fo"
os.makedirs(fo_dir, exist_ok=True)


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
    days_ahead = 2 - input_date.weekday()  # Thursday is 3
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


def download_and_extract_zip(url, extract_path):
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Upgrade-Insecure-Requests": "1",
    }

    # First get the cookies from NSE homepage
    session = requests.Session()
    print("Getting Cookies")
    response = session.get("https://www.nseindia.com", headers=headers)
    time.sleep(2)

    # Now download the file using the same session
    if response.status_code == 200:
        response = session.get(url, headers=headers, timeout=30)

        if response.ok:
            # print("Extracting files")
            z = zipfile.ZipFile(io.BytesIO(response.content))
            file_list = z.namelist()
            op_files = [f for f in file_list if f.lower().startswith("op")]
            for file in op_files:
                z.extract(file, extract_path)
            z.close()
            return True
    return False


def add_downloaded_info(df):
    is_downloaded = []
    filenames = []
    cleanded_filenames = []
    for row in df.iterrows():
        file_name = f"op{row[1]['date'].strftime('%d%m%y')}.csv"
        cleaned_file_name = f"op{row[1]['date'].strftime('%d%m%y')}_cleaned.csv"
        if os.path.exists(os.path.join(fo_dir, file_name)):
            is_downloaded.append(True)
            if os.path.exists(os.path.join(fo_dir, cleaned_file_name)):
                pass
            else:
                file_df = pd.read_csv(os.path.join(fo_dir, file_name))
                file_df = file_df[file_df["CONTRACT_D"].str.contains("OPTIDXNIFTY")]
                file_df = file_df[~file_df["CONTRACT_D"].str.contains("OPTIDXNIFTYNXT")]
                file_df.to_csv(os.path.join(fo_dir, cleaned_file_name), index=False)
            cleanded_filenames.append(cleaned_file_name)
        else:
            is_downloaded.append(False)
            cleanded_filenames.append("NA")
        filenames.append(file_name)

    df["downloaded_filename"] = filenames
    df["cleaned_filename"] = filenames
    df["downloaded"] = is_downloaded

    return df


if __name__ == "__main__":
    # download_latest_nifty_data()
    df = parse_nifty_data_to_dataframe()
    df = select_expiry_dates(df)
    df = add_downloaded_info(df)

    print(df.tail())
    df.to_csv("data.csv", header=True, index=False)

    # nifty_opt_puts = get_history(
    #     symbol="NIFTY",
    #     start=datetime.datetime.strptime("2024-11-29", "%Y-%m-%d"),
    #     end=datetime.datetime.strptime("2024-12-02", "%Y-%m-%d"),
    #     index=True,
    #     option_type="PE",
    #     strike_price=24100,
    #     expiry_date=datetime.datetime.strptime("2024-12-05", "%Y-%m-%d"),
    # )

    # base_url = "https://www.nseindia.com/api/reports"
    # archives = (
    #     quote(r'[{"name":"F&O - Bhavcopy ')
    #     + "(fo.zip)"
    #     + quote(r'","type":"archives","category":"derivatives","section":"equity"}]')
    # )
    # url = f"{base_url}?archives={archives}&date=25-Nov-2024&type=equity&mode=single"
    # print(url)
    # download_and_extract_zip(url, fo_dir)