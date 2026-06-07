def calculate_weight_change(df):
    if len(df) >= 2:
        latest_weight = df.iloc[-1]["weight"]
        previous_weight = df.iloc[-2]["weight"]
        change = latest_weight - previous_weight
        return f"{change:.1f} kg"

    return "No previous data"