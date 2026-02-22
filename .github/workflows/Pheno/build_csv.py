import pandas as pd
import numpy as np
import re
import os
from datetime import datetime

###############################################################################
# CONFIGURATION
###############################################################################

# Output filename
OUTPUT_FILE = "PHENOLOGY_LONG_FORMAT.csv"

# Columns for final long-format dataset
COLUMNS = [
    "OBSERVATIONDATETIME",
    "LOCATION",
    "WEDGE",
    "CATEGORY",
    "COMMONNAME",
    "SCIENTIFICNAME",
    "STATUS",
    "NOTES"
]

# USDA scientific name lookup (expand as needed)
USDA = {
    "frogfruit": "Phyla nodiflora",
    "calyophus": "Oenothera capillifolia",
    "chili pequin": "Capsicum annuum",
    "silver ponyfoot": "Dichondra argentea",
    "mealy blue sage": "Salvia farinacea",
    "esperanza": "Tecoma stans",
    "gregg dalea": "Dalea greggii",
    "damianita": "Chrysactinia mexicana",
    "tropical sage": "Salvia coccinea",
    "lyre leaf sage": "Salvia lyrata",
    "standing winecup": "Callirhoe pedata",
    "blue mistflower": "Conoclinium coelestinum",
    "prairie verbinia": "Glandularia bipinnatifida",
    "autumn sage": "Salvia greggii",
    "apache plume": "Fallugia paradoxa",
    "lindhiemer muhly": "Muhlenbergia lindheimeri",
    "am. beautyberry": "Callicarpa americana",
    "snakeherb": "Dyschoriste linearis",
    "pink guara": "Gaura lindheimeri",
    "white mistflower": "Ageratina havanensis",
    "zexmenia": "Wedelia acapulcensis",
    "red yucca": "Hesperaloe parviflora",
    "mountain pea": "Lathyrus latifolius",
    "milkweed rue": "Thamnosma texana",
    "beebalm": "Monarda fistulosa",
    "dwarf barb. cherry": "Prunus minutiflora",
    "buttonbush": "Cephalanthus occidentalis",
    "texas lantana": "Lantana urticoides",
    "globe mallow": "Sphaeralcea ambigua",
    "engelmann daisy": "Engelmannia peristenia",
    "obedient plant": "Physostegia virginiana",
    "straggler daisy": "Calyptocarpus vialis",
    "gayfeather": "Liatris punctata",
    "sk.leaf goldeneye": "Viguiera stenoloba",
    "chocolate daisy": "Berlandiera lyrata",
    "flame acanthus": "Anisacanthus quadrifidus",
    "rock rose": "Pavonia lasiopetala",
    "datura": "Datura wrightii",
    "black dalea": "Dalea frutescens",
    "fall aster": "Symphyotrichum ericoides",
    # Add more as needed
}

###############################################################################
# HELPERS
###############################################################################

def clean_name(name):
    if not isinstance(name, str):
        return ""
    return name.strip().lower()

def scientific_name(common):
    key = clean_name(common)
    return USDA.get(key, "")

def extract_date(cell):
    if isinstance(cell, datetime):
        return cell.date()
    if isinstance(cell, str):
        try:
            return pd.to_datetime(cell).date()
        except:
            return None
    return None

def is_wedge_row(value):
    return isinstance(value, (int, float)) and not pd.isna(value)

###############################################################################
# PARSE A SINGLE GARDEN FILE
###############################################################################

def parse_garden(filepath):
    df = pd.read_excel(filepath, header=None)
    rows = []

    # Identify date columns
    date_cols = {}
    for col in df.columns:
        for row in df[col]:
            d = extract_date(row)
            if d:
                date_cols[col] = d
                break

    # Parse wedge rows
    for i in range(len(df)):
        row = df.iloc[i]
        wedge = row[0]

        if not is_wedge_row(wedge):
            continue

        for col, date in date_cols.items():
            common = row[col]
            if isinstance(common, str) and common.strip() != "":
                status = row[col + 1] if (col + 1) in df.columns else ""
                rows.append({
                    "OBSERVATIONDATETIME": date,
                    "LOCATION": "Garden",
                    "WEDGE": int(wedge),
                    "CATEGORY": "Plant",
                    "COMMONNAME": common.strip(),
                    "SCIENTIFICNAME": scientific_name(common),
                    "STATUS": status if isinstance(status, str) else "",
                    "NOTES": ""
                })

    return pd.DataFrame(rows)

###############################################################################
# PARSE A SANCTUARY FILE
###############################################################################

def parse_sanctuary(filepath):
    df = pd.read_excel(filepath, header=None)
    rows = []

    # Identify date columns
    date_cols = {}
    for col in df.columns:
        for row in df[col]:
            d = extract_date(row)
            if d:
                date_cols[col] = d
                break

    # Sanctuary bloom lists
    for col, date in date_cols.items():
        for i in range(len(df)):
            cell = df.iloc[i, col]
            if isinstance(cell, str) and cell.strip() != "":
                rows.append({
                    "OBSERVATIONDATETIME": date,
                    "LOCATION": "Sanctuary",
                    "WEDGE": "",
                    "CATEGORY": "Plant",
                    "COMMONNAME": cell.strip(),
                    "SCIENTIFICNAME": scientific_name(cell),
                    "STATUS": "Blooming",
                    "NOTES": ""
                })

    return pd.DataFrame(rows)

###############################################################################
# MAIN MERGE
###############################################################################

def main():
    all_rows = []

    for file in sorted(os.listdir(".")):
        if not file.lower().endswith(".xlsx"):
            continue

        if "sanctuary" in file.lower():
            df = parse_sanctuary(file)
        else:
            df = parse_garden(file)

        all_rows.append(df)

    final = pd.concat(all_rows, ignore_index=True)

    # Sort chronologically
    final = final.sort_values(by="OBSERVATIONDATETIME")

    # Ensure all columns exist
    for col in COLUMNS:
        if col not in final.columns:
            final[col] = ""

    final = final[COLUMNS]

    # Output CSV
    final.to_csv(OUTPUT_FILE, index=False, encoding="utf-8", line_terminator="\n")

    print("DONE — CSV generated:", OUTPUT_FILE)

###############################################################################

if __name__ == "__main__":
    main()
