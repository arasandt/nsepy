import datetime
import sys
import pandas as pd
from glob import glob
import math
import json
import os

options_data_folder = "fo"
nifty_json = "nifty_json_data.json"


def validate_date(date_str):
    if not date_str:  # Handles both None and empty string
        return False
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_upcoming_expiry_date():
    current_month_year = datetime.datetime.now().strftime("%m%y")
    pattern = f"{options_data_folder}/*{current_month_year}_cleaned.csv"

    # Find the latest date by extracting dates from filenames and converting to datetime
    max_date_file = max(
        int(
            file.split("_")[0].split("/op")[-1][4:]
            + file.split("_")[0].split("/op")[-1][2:4]
            + file.split("_")[0].split("/op")[-1][:2]
        )
        for file in glob(pattern)
    )
    max_date_file = datetime.datetime.strptime(str(max_date_file), "%y%m%d")
    print(f"Data loaded until : {max_date_file.date()}")

    for file in glob(pattern):
        df = pd.read_csv(file)
        df["CONTRACT_D_NEW"] = pd.to_datetime(
            df["CONTRACT_D"].str[11:22], format="%d-%b-%Y"
        )
        mask = df["CONTRACT_D_NEW"] >= datetime.datetime.now()
        if mask.any():
            return df.loc[mask, "CONTRACT_D_NEW"].min().strftime("%Y-%m-%d")

    return None


def get_date_input(prompt, default_value):
    date = input(f"Please enter {prompt} ({default_value}) : ")
    return date if date else default_value


def validate_and_print(date, date_type):
    if not validate_date(date):
        print(f"Date {date} for {date_type} is invalid. Please use YYYY-MM-DD format")
        raise Exception(f"Invalid {date_type} date")


def conditional_round_100(x):
    remainder = x % 100
    if remainder >= 50:
        return math.ceil(x / 100) * 100
    return math.floor(x / 100) * 100


def parse_nifty_data_to_dataframe():
    with open("nifty_json_data.json", "r") as f:
        data = json.loads(f.read())

    df = pd.DataFrame()
    df["unixtimestamp"] = data["chart"]["result"][0]["timestamp"]
    df["date"] = df["unixtimestamp"].apply(
        lambda x: datetime.datetime.fromtimestamp((x))
    )
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["high"] = data["chart"]["result"][0]["indicators"]["quote"][0]["high"]
    df["low"] = data["chart"]["result"][0]["indicators"]["quote"][0]["low"]
    df["close"] = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    return df


def get_strike_price_for_start_date(df, start_date):
    df = df[df["date"] == datetime.datetime.strptime(start_date, "%Y-%m-%d")]
    if not len(df):
        print(f"No data found for {start_date}. Please change dates and try again.")
        sys.exit(1)
    close_price = df["close"].values[0]
    return conditional_round_100(close_price), round(close_price, 2)


def main():
    upcoming_expiry_date = get_upcoming_expiry_date()
    default_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # start_date = get_date_input("start date", default_date)
    # expiry_date = get_date_input("expiry date", upcoming_expiry_date)
    start_date = "2024-12-02"
    expiry_date = "2024-12-05"

    try:
        validate_and_print(start_date, "start")
        validate_and_print(expiry_date, "expiry")
    except Exception:
        sys.exit(1)

    nifty_data_df = parse_nifty_data_to_dataframe()
    strike_price, close_price = get_strike_price_for_start_date(
        nifty_data_df, start_date
    )
    print(f"Strike price selected for {start_date} ({close_price}) : {strike_price} ")

    # from next day to start_date get price for call and put options. the data is present in fo/opDDMMDD.csv file.
    # Get the next day after start_date

    # Get all files between start_date and expiry_date
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")

    data_for_dates = pd.DataFrame()
    current_dt = start_date

    while current_dt <= expiry_date:
        date_str = current_dt.strftime("%d%m%y")
        file_path = f"{options_data_folder}/op{date_str}_cleaned.csv"
        if os.path.exists(file_path):

            df = pd.read_csv(file_path)
            # Check if any records match the expiry date
            df["CONTRACT_D_NEW"] = pd.to_datetime(
                df["CONTRACT_D"].str[11:22], format="%d-%b-%Y"
            )
            if not (df["CONTRACT_D_NEW"] == expiry_date).any():
                print(f"Expiry date {expiry_date.date()} is invalid")
                sys.exit(1)

            print(f"Reading data for {current_dt.date()}")

            df.drop(
                columns=[
                    "NOTIONAL_V",
                    "TRADED_QUA",
                    "UNDRLNG_ST",
                    "PREMIUM_TR",
                    "SETTLEMENT",
                    "OPEN_PRICE",
                    "PREVIOUS_S",
                    # "CLOSE_PRIC",
                    "NET_CHANGE",
                    "OI_NO_CON",
                    "TRD_NO_CON",
                ],
                inplace=True,
                axis=1,
            )
            df["FILE_DATE"] = datetime.datetime.strptime(date_str, "%d%m%y")
            data_for_dates = pd.concat([data_for_dates, df], ignore_index=True)
        current_dt += datetime.timedelta(days=1)

    if not len(data_for_dates):
        print(f"No options data files found between {start_date} and {expiry_date}")
        sys.exit(1)

    data_for_dates["STRIKE_PRICE"] = pd.to_numeric(
        data_for_dates["CONTRACT_D"].str[24:], errors="coerce"
    )
    data_for_dates["EXPIRY_DATE"] = pd.to_datetime(
        data_for_dates["CONTRACT_D"].str[11:22], format="%d-%b-%Y"
    )
    data_for_dates["OPTION_TYPE"] = data_for_dates["CONTRACT_D"].str[22:24]

    data_for_dates = data_for_dates[data_for_dates["STRIKE_PRICE"] == strike_price]
    data_for_dates = data_for_dates[data_for_dates["EXPIRY_DATE"] == expiry_date]
    # print(data_for_dates.head(5))

    data_for_dates_swap = data_for_dates.copy()

    high_price = []
    low_price = []

    for row in data_for_dates_swap.iterrows():
        if row[1]["OPTION_TYPE"] == "CE":
            low_price.append(row[1]["HIGH_PRICE"])
            high_price.append(row[1]["LOW_PRICE"])
        else:
            low_price.append(row[1]["LOW_PRICE"])
            high_price.append(row[1]["HIGH_PRICE"])

    data_for_dates_swap["HIGH_PRICE"] = high_price
    data_for_dates_swap["LOW_PRICE"] = low_price

    # print(data_for_dates_swap.head(5))

    grouped_data = (
        data_for_dates_swap.groupby(["FILE_DATE", "STRIKE_PRICE", "EXPIRY_DATE"])[
            ["CLOSE_PRIC", "HIGH_PRICE", "LOW_PRICE"]
        ]
        .sum()
        .reset_index()
    )

    grouped_data = pd.merge(
        grouped_data,
        nifty_data_df[["date", "close"]],
        left_on="FILE_DATE",
        right_on="date",
        how="left",
    )[grouped_data.columns.tolist() + ["close"]].rename(
        columns={"close": "NIFTY_CLOSE"}
    )
    grouped_data["NIFTY_CLOSE"] = round(grouped_data["NIFTY_CLOSE"], 2)

    grouped_data = grouped_data.rename(
        columns={"HIGH_PRICE": "MAX_1", "LOW_PRICE": "MAX_2"}
    )

    grouped_data["POSITION_PRICE"] = grouped_data.groupby("EXPIRY_DATE")[
        "CLOSE_PRIC"
    ].transform("first")
    grouped_data["POSITION_PRICE_DATE"] = grouped_data.groupby("EXPIRY_DATE")[
        "FILE_DATE"
    ].transform("first")

    grouped_data.loc[
        grouped_data["POSITION_PRICE_DATE"] == grouped_data["FILE_DATE"],
        ["MAX_1", "MAX_2"],
    ] = 0

    grouped_data["POSITION_PL"] = (
        grouped_data["CLOSE_PRIC"] - grouped_data["POSITION_PRICE"]
    ) * 25

    grouped_data["POSITION_PL_MAX_1"] = (
        grouped_data["MAX_1"] - grouped_data["POSITION_PRICE"]
    ) * 25
    grouped_data["POSITION_PL_MAX_2"] = (
        grouped_data["MAX_2"] - grouped_data["POSITION_PRICE"]
    ) * 25

    grouped_data.loc[
        grouped_data["POSITION_PRICE_DATE"] == grouped_data["FILE_DATE"],
        ["MAX_1", "MAX_2", "POSITION_PL_MAX_1", "POSITION_PL_MAX_2"],
    ] = 0

    grouped_data = grouped_data.reindex(
        columns=[
            "FILE_DATE",
            "NIFTY_CLOSE",
            "STRIKE_PRICE",
            "EXPIRY_DATE",
            "POSITION_PRICE",
            # "POSITION_PRICE_DATE",
            "CLOSE_PRIC",
            "MAX_1",
            "MAX_2",
            "POSITION_PL",
            "POSITION_PL_MAX_1",
            "POSITION_PL_MAX_2",
        ]
    )

    print(grouped_data)

    # next_day = datetime.datetime.strptime(start_date, "%Y-%m-%d") + datetime.timedelta(
    #     days=1
    # )
    # next_day_str = next_day.strftime("%d%m%y")

    # # Read options data file for next day
    # options_file = f"{options_data_folder}/op{next_day_str}_cleaned.csv"
    # if not os.path.exists(options_file):
    #     print(f"Options data file not found for {next_day_str}")
    #     sys.exit(1)

    # # Read options data into dataframe
    # options_df = pd.read_csv(options_file)

    # # Filter for selected strike price
    # strike_options = options_df[options_df["STRIKE_PR"] == strike_price]

    # # Get call and put option prices
    # call_options = strike_options[strike_options["OPTION_TYP"] == "CE"]
    # put_options = strike_options[strike_options["OPTION_TYP"] == "PE"]

    # if len(call_options) > 0:
    #     print(
    #         f"Call option price for strike {strike_price}: {call_options['CLOSE'].values[0]}"
    #     )
    # if len(put_options) > 0:
    #     print(
    #         f"Put option price for strike {strike_price}: {put_options['CLOSE'].values[0]}"
    #     )


if __name__ == "__main__":
    main()
