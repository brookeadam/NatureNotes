import pandas as pd
import numpy as np

# Sample eBird data
ebird_data = pd.DataFrame({
    "Date": pd.date_range(start="2024-01-01", periods=10, freq='D'),
    "Species": [
        "Northern Cardinal", "Blue Jay", "Carolina Wren", "Red-shouldered Hawk",
        "Mourning Dove", "Eastern Phoebe", "Great Egret", "Ruby-throated Hummingbird",
        "American Robin", "Black-crested Titmouse"
    ],
    "Count": [2, 3, 1, 1, 5, 2, 1, 1, 4, 2],
    "Location ID": ["L1210588", "L1210849"] * 5,
    "Observer": ["Brooke Adam"] * 10
})

# Sample weather data matched to dates
weather_data = pd.DataFrame({
    "Date": pd.date_range(start="2024-01-01", periods=10, freq='D'),
    "Max Temp (F)": np.random.randint(60, 95, size=10),
    "Min Temp (F)": np.random.randint(40, 65, size=10),
    "Precipitation (in)": np.round(np.random.uniform(0, 0.5, size=10), 2)
})

# Save files to a zip archive
ebird_path = "/mnt/data/ebird_data.csv"
weather_path = "/mnt/data/weather_data.csv"
zip_path = "/mnt/data/nature_notes_data.zip"

ebird_data.to_csv(ebird_path, index=False)
weather_data.to_csv(weather_path, index=False)

import zipfile
with zipfile.ZipFile(zip_path, 'w') as zipf:
    zipf.write(ebird_path, arcname="data/ebird_data.csv")
    zipf.write(weather_path, arcname="data/weather_data.csv")

zip_path
