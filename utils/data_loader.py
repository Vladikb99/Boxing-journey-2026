import pandas as pd
from datetime import date


def load_weight_data():
    return pd.read_csv("data/weight.csv")


def get_latest_weight():
    df = load_weight_data()
    return df.iloc[-1]["weight"]


def save_weight(weight):
    df = load_weight_data()

    new_row = {
        "date": date.today().isoformat(),
        "weight": weight
    }

    df.loc[len(df)] = new_row
    df.to_csv("data/weight.csv", index=False)