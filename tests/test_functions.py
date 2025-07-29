import pandas as pd

def parse_time(time_str):
    if not time_str or time_str == 'N/A' or time_str.strip() == '':
        return None
    try: # hour value * 12 + minute value (12 hour clock, do not include am/pm)
        hour = time_str.split(":")[0]
        minute = time_str.split(":")[1].lower().rstrip("apm")
        return int(hour) * 60 + int(minute)
    except (ValueError, TypeError):
        return None

# print(parse_time("10:50am"))
# print(parse_time("12:20pm"))
# print(parse_time("10:50am"))


df = pd.read_csv("2025-Spring.csv")
# print(len(df))

print(df["type"].unique())