import csv
import yaml
from datetime import datetime
from tkinter import Tk, filedialog
from tqdm import tqdm

def select_csv_file() -> str:
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    csv_file = filedialog.askopenfilename(title="Select CSV file", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
    root.destroy()
    return csv_file

def process_data(reader, filter_row_index:int, filter_condition:str, progress_bar) -> list[dict]:
    filtered_data = []
    for row in progress_bar(reader):
        if row[headers[filter_row_index]] == filter_condition:
            filtered_data.append({"start": datetime.strptime(row['Time'], "%Y.%m.%d %H:%M:%S"), "value": float(row['Value [kWh]'])})
    return filtered_data

def process_day_data(day_data, filter_data, progress_bar) -> list[dict]:
    yaml_data = []
    for day in progress_bar(day_data):
        day_start = day["start"]
        day_values = [value for value in filter_data if value["start"].date() == day_start.date()]
        day_start_value = day["value"]
        prev_value = day_start_value
        for i in day_values:
            timestamp = i["start"]
            if timestamp.minute == 0:
                yaml_data.append({
                    'start': timestamp.strftime('%Y-%m-%d %H:%M:%S+02:00'),
                    'state': round(prev_value, 2),
                    'sum': round(prev_value, 2)
                    })
            prev_value += i["value"]
    return yaml_data

if __name__ == "__main__":
    csv_file_path = select_csv_file()
    if csv_file_path:
        with open(csv_file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            headers = reader.fieldnames
            data_ap = process_data(reader, 1, "'+A'", tqdm)
            f.seek(0)  # Reset file pointer
            data_an = process_data(reader, 1, "'-A'", tqdm)
            f.seek(0)  # Reset file pointer
            data_dp_ap = process_data(reader, 1, "'DP_1-1:1.8.0*0'", tqdm)
            f.seek(0)  # Reset file pointer
            data_dp_an = process_data(reader, 1, "'DP_1-1:2.8.0*0'", tqdm)
        
        yaml_data_ap = process_day_data(data_dp_ap, data_ap, tqdm)
        yaml_data_an = process_day_data(data_dp_an, data_an, tqdm)

        with open("import.yaml", 'w') as f:
            yaml.dump(yaml_data_ap, f)

        with open("export.yaml", 'w') as f:
            yaml.dump(yaml_data_an, f)
