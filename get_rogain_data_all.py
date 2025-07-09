from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

# Load the HTML file
html_path = "WRC 2025 - Parciales.html"
with open(html_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Find all tables
tables = soup.find_all("table")

# Data holder for all teams
all_data = []

# Process all teams (look for width="1381px" markers)
for idx, table in enumerate(tables):
    if table.get("width") == "1381px":
        team_cell = table.find("td", {"id": "c13"})
        if not team_cell:
            continue

        team = team_cell.get_text(strip=True).upper()
        if not team:
            continue

        # Try to get next table (results table)
        if idx + 1 >= len(tables):
            continue
        result_table = tables[idx + 1]

        # Extract data
        points = []
        times = []
        total_points = []
        total = 0

        rows = result_table.find_all("tr")
        points_row = None
        times_row = None

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            row_values = [col.get_text(strip=True) for col in cols[1:]]

            # Check for points row
            if all(
                val == "" or val.upper() == "META" or re.match(r".*\(\d+\)", val)
                for val in row_values
            ):
                points_row = []
                for val in row_values:
                    if val == "" or val.upper() == "META":
                        continue
                    try:
                        score = int(val.split("(")[-1].replace(")", ""))
                        points_row.append(score)
                    except:
                        continue

            # Check for time row
            elif all(val == "" or re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", val) for val in row_values):
                times_row = []
                for val in row_values:
                    if val == "":
                        continue
                    try:
                        if val.count(":") == 2:
                            time_obj = datetime.strptime(val, "%H:%M:%S").time()
                        elif val.count(":") == 1:
                            time_obj = datetime.strptime("00:" + val, "%H:%M:%S").time()
                        else:
                            continue
                        times_row.append(time_obj)
                    except:
                        continue

                if points_row is not None:
                    for pt, ts in zip(points_row, times_row):
                        points.append(pt)
                        times.append(ts)
                        total += pt
                        total_points.append(total)
                    points_row = None
                    times_row = None

        # Store team data
        for pt, ts, tp in zip(points, times, total_points):
            all_data.append({
                "Team": team,
                "Points": pt,
                "Time": ts,
                "Total points": tp
            })

# Convert all data to DataFrame
df = pd.DataFrame(all_data)

# Save to a single CSV
output_file = "all_teams_points_by_time.csv"
df.to_csv(output_file, index=False)
print(f"Saved: {output_file}")
