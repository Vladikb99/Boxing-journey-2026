import pandas as pd


def load_weight_data():
    """Load all weight data from CSV."""
    return pd.read_csv("data/weight.csv")


def get_latest_weight():
    """Return the latest weight."""
    df = load_weight_data()
    return df.iloc[-1]["weight"]