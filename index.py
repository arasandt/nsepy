import datetime
import sys
import pandas as pd
from glob import glob

options_data_folder = "fo"


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


def main():
    upcoming_expiry_date = get_upcoming_expiry_date()
    default_date = datetime.datetime.now().strftime("%Y-%m-%d")

    start_date = get_date_input("start date", default_date)
    expiry_date = get_date_input("expiry date", upcoming_expiry_date)

    try:
        validate_and_print(start_date, "start")
        validate_and_print(expiry_date, "expiry")
    except Exception as error:
        sys.exit(1)


if __name__ == "__main__":
    main()
