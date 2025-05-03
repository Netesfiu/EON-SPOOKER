import csv
import yaml
import os
from datetime import datetime, timezone
from tkinter import Tk, filedialog
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description="Convert E.ON CSV data to YAML")
parser.add_argument("-p", "--path", metavar='"path.csv"', help="path for the input file", required=False)

def select_csv_file() -> str:
    csv_file = parser.parse_args().path
    if csv_file:
        if not os.path.exists(csv_file):
            raise FileNotFoundError("File not found. Please check the file path.")
        elif not csv_file.endswith(".csv"):
            raise ValueError("Invalid file type. Please select a CSV file.")
        return csv_file
    else:
        if os.environ.get('DISPLAY','') is None:
            raise EnvironmentError('Unable to run without a GUI. Use the "--path" argument to define the filepath')
        else:
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            csv_file = filedialog.askopenfilename(title="Select CSV file", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
            root.destroy()
            if not csv_file:
                raise ValueError("No file selected")
            if not csv_file.endswith(".csv"):
                raise ValueError("Invalid file type. Please select a CSV file.")
            return csv_file

def process_data(reader, filter_row_index:int, filter_condition:str, progress_bar, desc:str) -> list[dict]:
    filtered_data = []
    for row in progress_bar(reader, desc=f"Processing {desc}"):
        if row[headers[filter_row_index]] == filter_condition:
            filtered_data.append({"start": datetime.strptime(row['Time'], "%Y.%m.%d %H:%M:%S"), "value": float(row['Value [kWh]'])})
    return filtered_data

def process_day_data(day_data, filter_data, progress_bar, desc:str) -> list[dict]:
    yaml_data = []
    for day in progress_bar(day_data, desc=f"Processing {desc} daily data"):
        day_start = day["start"]
        day_values = [value for value in filter_data if value["start"].date() == day_start.date()]
        day_start_value = day["value"]
        prev_value = day_start_value
        for i in day_values:
            timestamp = i["start"]
            if timestamp.minute == 0:
                # Get local timezone offset
                tz_offset = datetime.now(timezone.utc).astimezone().strftime('%z')
                tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"  # Insert colon between hours and minutes
                yaml_data.append({
                    'start': f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}{tz_offset}",
                    'state': round(prev_value, 2),
                    'sum': round(prev_value, 2)
                    })
            prev_value += i["value"]
    return yaml_data

if __name__ == "__main__":
    csv_file_path = select_csv_file()
    if csv_file_path:
        # First read headers to make them available globally
        with open(csv_file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            global headers
            headers = reader.fieldnames

        with open(csv_file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            data_ap = process_data(reader, 1, "'+A'", tqdm, "import data")
            f.seek(0)
            data_an = process_data(reader, 1, "'-A'", tqdm, "export data")
            f.seek(0)
            data_dp_ap = process_data(reader, 1, "'DP_1-1:1.8.0*0'", tqdm, "import daily data")
            f.seek(0)
            data_dp_an = process_data(reader, 1, "'DP_1-1:2.8.0*0'", tqdm, "export daily data")
        
        yaml_data_ap = process_day_data(data_dp_ap, data_ap, tqdm, "import")
        yaml_data_an = process_day_data(data_dp_an, data_an, tqdm, "export")

        with open("import.yaml", 'w') as f:
            yaml.dump(yaml_data_ap, f)

        with open("export.yaml", 'w') as f:
            yaml.dump(yaml_data_an, f)
