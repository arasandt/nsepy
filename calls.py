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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# from nsepy import get_history
from urllib.parse import quote, urlencode, quote_plus

lookback_in_months = 12
nifty_json_data = "nifty.json"

fo_dir = "fo"
os.makedirs(fo_dir, exist_ok=True)


def create_session_with_retry():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


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
    print(url)
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
    date_mapping = pd.Series(index=thursdays, dtype="datetime64[ns]")

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
    print(url)
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Prioriy": "u=0, i",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Upgrade-Insecure-Requests": "1",
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        # "Cookie": '_ga=GA1.1.344521966.1731251502; defaultLang=en; AKA_A2=A; nsit=pR6P8iFtVz7wg15U2e6p-g0t; nseappid=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcGkubnNlIiwiYXVkIjoiYXBpLm5zZSIsImlhdCI6MTczMzMyNjI0MCwiZXhwIjoxNzMzMzMzNDQwfQ.wwfqIQU5YmAts-lGyDh5-aTHBff2hVsNyLIjesqNyP8; bm_mi=DAAF7707D66AF0D253A8293B57642681~YAAQJgosF4FcmSeTAQAAJ35LkhqsooFvruDNzIKI+mpcMVy/3EsPeKNOfx+0D2bYKhazs7QelI2hsG1HhKqK3cbRoaU3ADvnLVSXCoGFC2kXSNG7/hucvlgykpoecDt98O85cLjYgnbKnuzpezjiJJO9KkWgXTa7KzU9unyeTDel1oaJhfVBUw2F52YWpeqxmBdyrmCv2Y1Yz+PJlRgA0nJbI7D7wOsZV59nMcIlSZR9RIwafXc9xXXjHsroFJNPPxVCzPtrZ0adAF0efq9DKYRGREjXYpPRYwauSnjwkIOPCP4TEpPAEAOQgGAWwVE=~1; _ga_87M7PJ3R97=GS1.1.1733326242.13.1.1733326242.60.0.0; _ga_WM2NSQKJEK=GS1.1.1733326242.13.0.1733326242.0.0.0; ak_bmsc=69041F58A5D9BACBAAFA96360BB6CD5D~000000000000000000000000000000~YAAQJgosFxFdmSeTAQAAYYRLkhrS5FFuGeIq17U4xOoDkba/2PCpEyXoNidCWv1i2LXDFiO6k2Dn6N/q2Zds73e5OaMRdV5lgTY3JsRr3aGRbaG8EB+vM6cEmhUM8fKRpFxd3OlHywoN9AG64YUdNIcGQ5RM31qMj2C9lOiPcd6Q3VXRGGFOGNJR7SaNL8zvcDjKEUmUD61+7YmGWvS5D9GXupmq+/kd07PHz6jDA1uk3uWhytfC2JW7qnk/utixkA/TKn0FpVRmpfnq3b5+SVMgrTB246lVJwonBPrQYJTGS6+iM4tKjJ0LDS2C2FwU57URYlaLassOs+gZBA907O/PRgsjyoOkvaUQ2I9/6jFP2LNMcTASyvOpMX6OLDiJ8SEU6S+uejC2J62Xws5N1Mn6AfgeE/nAl9kCVxUnD4xcN1sak0iDQ6a+IMvrY/Z8yxs88HpFGIYIq7wXFkQid5D9sLRJRzYda6pRlqKa3w==; bm_sz=C8E939D669E85D1E2683F2C26C59836C~YAAQJgosF0YqmieTAQAAnvZXkhpUt7/cA9pLc9lCBN8RIZc+gGLUHhnUYOlM237RyVWsCKB8DjiO3JQMW2H518JF0UiEre6XZdKXjRIaWMquygJPdVcO/vgnuMI7dKqMmsg8RKQ6e0F0lOTKmiu0fdOnfBtV9CKRGrX2XwFgL2m6qXeGbzBYVcXvs1Lqmv6ck1tr4vWsAsluXtWHeo13JA/LouDLL+1/C0oJ0gHBMqLxpnzjadL+QHoCqoG1P07V1LEamBN7Tq3z1VlGQ+Lwts1IFLh7Y1n+gT7jTFXOfgNIa6TWiRBUJ/wu5Y8FBkdxQjur+Xm/AyM0MvsNGCkV137cKZR+8Jy9GVIKySJGuMp8+qxAxAFGoBt930BbzMzJuPzMdVKL70nxNr2shQE4UxrlXtyOrgRl6ojFNFRiDFWk48amDuef~4602162~4338244; _abck=AEEE8321135827883310C0ADD706330D~0~YAAQJgosF8xAmieTAQAAFrVZkg0RCq2MCq1I24XqqACyDihYAEvLJhme4YlXeOo424SevRhlvMOw4NjlcxKM4jjeoqbJLuNuz/AiJdKqkfxzB3mY2qOUOWeJPKVrtRIeeJ37qMV0TULw/prHI8+NoZFlwG/fj5xy8pTYA8FHPgKNAt85M+hAQ5zvJuIgMhrdTwmw3inSGNDiBcEyE/DKzP2OuHHRlcWYZ2Jd/eK/kinVxmmajTy2uI9WJJ/f6pKVmtZv+/eXcT8O7doeuacwcSA4oDyjRYkIfAOdZJgKVlIKRVL/JVlXgLzNGnX4gNhWwT4pVvMnOtFV2OawkkDwUzSrKCNyM50RoeRJTO3AVqyy+8da6Ijazwk5isnY9QFuNsfyVrUquq1QGQTaDYC27c0qn1uqnhUk2pYnZR2UTIrOAqQuxBnVkLbJp1eS4KDP0Og+oH8fSNS/~-1~-1~-1; bm_sv=D6B4850E4102CFFFD4549C3826F5D5D7~YAAQJgosF81AmieTAQAAFrVZkhox+BNAFOSA/3RiyGGIU9DFfaa4kKYDUGX6CSV2Azvh73343JJfFhe0xbE/lVnsAT0Gsm/vwq0cwduLg7f5H4Jmyu1IXhvTluYbaxx7po1+unVZn6IpSwUcO4HO0NPAXilvkao7E3mcb7qFwZdn6Cbc5lPRLboCgul1pRpRwbE7S192S6EfQw0InJIpGEjRdn47A9w5cP7at7XYRBE0pBbfA9yIEz5LBPy6eLqA1VhM~1; RT="z=1&dm=nseindia.com&si=0efd09cc-a954-447b-ac77-3cc0cfadc029&ss=m4a1ov1u&sl=0&se=8c&tt=0&bcn=%2F%2F684d0d48.akstat.io%2F&ul=k17v"',
    }

    # First get the cookies from NSE homepage
    session = requests.Session()
    # session = create_session_with_retry()
    # print("Getting Cookies")
    try:
        response = session.get(
            "https://www.nseindia.com", headers=headers, timeout=(5, 30)
        )
        time.sleep(2)

        # Now download the file using the same session
        if response.status_code == 200:
            response = session.get(url, headers=headers, timeout=(5, 30), stream=True)
            print(url)
            if response.ok:
                # print("Extracting files")
                z = zipfile.ZipFile(io.BytesIO(response.content))
                file_list = z.namelist()
                op_files = [f for f in file_list if f.lower().startswith("op")]
                for file in op_files:
                    z.extract(file, extract_path)
                z.close()
                return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading: {str(e)}")
        time.sleep(5)  # Wait before retry
    return False


def add_downloaded_info(df):
    is_downloaded = []
    filenames = []
    cleaned_filenames = []
    for row in df.iterrows():

        file_name = f"op{row[1]['date'].strftime('%d%m%y')}.csv"
        # print(f"Working on {file_name}")
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
            cleaned_filenames.append(cleaned_file_name)
        else:
            # print("Downloading Option Chain")
            download_options_chain(row[1]["date"])
            if os.path.exists(os.path.join(fo_dir, file_name)):
                is_downloaded.append(True)
            else:
                is_downloaded.append(False)
            cleaned_filenames.append("NA")
        filenames.append(file_name)

    df["downloaded_filename"] = filenames
    df["cleaned_filename"] = cleaned_filenames
    df["downloaded"] = is_downloaded

    return df


def download_options_chain(row):
    base_url = "https://www.nseindia.com/api/reports"
    archives = (
        quote(r'[{"name":"F&O - Bhavcopy ')
        + "(fo.zip)"
        + quote(r'","type":"archives","category":"derivatives","section":"equity"}]')
    )

    print("Downloading", row.strftime("%d-%b-%Y"))
    trade_date = row.strftime("%d%b%y")
    url = f"{base_url}?archives={archives}&date={trade_date}&type=equity&mode=single"
    download_and_extract_zip(url, fo_dir)


def add_strike_price_data(df):
    strike_price_call = []
    strike_price_call_high = []
    strike_price_call_low = []
    strike_price_put = []
    strike_price_put_high = []
    strike_price_put_low = []
    strike_price_call_name = []
    strike_price_put_name = []
    df["strike_price_call_name"] = 0
    df["strike_price_call"] = 0
    df["strike_price_call_high"] = 0
    df["strike_price_call_low"] = 0
    df["strike_price_put_name"] = 0
    df["strike_price_put"] = 0
    df["strike_price_put_high"] = 0
    df["strike_price_put_low"] = 0
    for row in df.iterrows():
        put_option_name = f"OPTIDXNIFTY{row[1]['expirydate'].strftime('%d-%b-%Y').upper()}PE{row[1]['strikeprice']}"
        call_option_name = f"OPTIDXNIFTY{row[1]['expirydate'].strftime('%d-%b-%Y').upper()}CE{row[1]['strikeprice']}"
        if row[1]["downloaded"]:
            file_name = os.path.join(fo_dir, row[1]["cleaned_filename"])
            if os.path.exists(file_name):
                file_df = pd.read_csv(file_name)
                # print(row[1])
                try:
                    put_option_price = file_df[
                        file_df["CONTRACT_D"] == put_option_name
                    ]["CLOSE_PRIC"].values[0]
                except:
                    put_option_price = 0
                try:
                    put_option_price_high = file_df[
                        file_df["CONTRACT_D"] == put_option_name
                    ]["HIGH_PRICE"].values[0]
                except:
                    put_option_price_high = 0
                try:
                    put_option_price_low = file_df[
                        file_df["CONTRACT_D"] == put_option_name
                    ]["LOW_PRICE"].values[0]
                except:
                    put_option_price_low = 0

                try:
                    call_option_price = file_df[
                        file_df["CONTRACT_D"] == call_option_name
                    ]["CLOSE_PRIC"].values[0]
                except:
                    call_option_price = 0
                try:
                    call_option_price_high = file_df[
                        file_df["CONTRACT_D"] == call_option_name
                    ]["HIGH_PRICE"].values[0]
                except:
                    call_option_price_high = 0
                try:
                    call_option_price_low = file_df[
                        file_df["CONTRACT_D"] == call_option_name
                    ]["LOW_PRICE"].values[0]
                except:
                    call_option_price_low = 0

                strike_price_call.append(call_option_price)
                strike_price_call_high.append(call_option_price_high)
                strike_price_call_low.append(call_option_price_low)

                strike_price_put.append(put_option_price)
                strike_price_put_high.append(put_option_price_high)
                strike_price_put_low.append(put_option_price_low)
            else:
                strike_price_call.append(0)
                strike_price_call_high.append(0)
                strike_price_call_low.append(0)

                strike_price_put.append(0)
                strike_price_put_high.append(0)
                strike_price_put_low.append(0)
        else:
            strike_price_call.append(0)
            strike_price_call_high.append(0)
            strike_price_call_low.append(0)

            strike_price_put.append(0)
            strike_price_put_high.append(0)
            strike_price_put_low.append(0)

        strike_price_call_name.append(call_option_name)
        strike_price_put_name.append(put_option_name)

    df["strike_price_call_name"] = strike_price_call_name
    df["strike_price_call"] = strike_price_call
    df["strike_price_call_high"] = strike_price_call_high
    df["strike_price_call_low"] = strike_price_call_low
    df["strike_price_put_name"] = strike_price_put_name
    df["strike_price_put"] = strike_price_put
    df["strike_price_put_high"] = strike_price_put_high
    df["strike_price_put_low"] = strike_price_put_low
    df["position_price"] = df["strike_price_call"] + df["strike_price_put"]
    df["position_price_max_1"] = (
        df["strike_price_put_low"] + df["strike_price_call_high"]
    )
    df["position_price_max_2"] = (
        df["strike_price_put_high"] + df["strike_price_call_low"]
    )
    return df


def run():

    df = parse_nifty_data_to_dataframe()
    df = select_expiry_dates(df)
    df = add_downloaded_info(df)

    df = add_strike_price_data(df)

    print(df.tail())
    count_df = df.groupby(df["date"].dt.month)["downloaded"].sum().reset_index()
    print(count_df.head(300))
    df.to_csv("NIFTY_data.csv", header=True, index=False)


if __name__ == "__main__":
    # download_latest_nifty_data()
    run()
    # for i in range(1000):
    # try:
    # run()
    # except Exception as e:
    # print(e)
    # pass
    # print(f"{i+1} : Waiting for 30 seconds and trying again")
    # time.sleep(30)
