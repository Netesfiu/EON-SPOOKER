Read in other languages: 
<kbd>[<img title="Magyar" alt="Magyar" src="https://cdn.statically.io/gh/hjnilsson/country-flags/master/svg/hu.svg" width="22">](languages/readme.hu.md)</kbd> 
<kbd> [<img title="English" alt="English" src="https://cdn.statically.io/gh/hjnilsson/country-flags/master/svg/us.svg" width="22">](languages/readme.en.md)</kbd>

# E.ON W1000 "Spooker"

This repository contains a Python script that can scrape raw data from the [E.ON W1000 portal](https://energia.eon-hungaria.hu/W1000/) and convert it to a raw YAML file. This YAML file can then be copied to the `recorder.import_statistics` service if you have the [frenck/Spook](https://github.com/frenck/spook) integration installed. I recommend using this with the [hass-w1000-portal](https://github.com/ZsBT/hass-w1000-portal) from ZsBT.

## Requirements

To run the script, you need to have the following dependencies installed:

- Python 3.12.0 (optional)
- Access to the E.ON W1000 portal
- [Spook](https://github.com/frenck/spook) installed
    - please refer to the [integration's documentation](https://spook.boo) for the installation

## Aquiring data from E.ON W1000

1. log in to your W1000 portal, [here](https://energia.eon-hungaria.hu/W1000/Account/Login).
2. Create a new workarea if you haven't created one
3. inside a workarea, create a new report with the "+" icon and add the following curves:
    - +A
    - -A
    - DP_1-1:1.8.0*0
    - DP_1-1:2.8.0*0
4. after clicking "ok" you should be able to see the data on the report
5. on the report pager click on the "day" and select "custom"
6. type in your report interval. it shouls be in `dd/mm/yyyy` format.
7. after you defined your date interval press the checkmark icon.
8. click on the "export" link in the report or choose the export option in the the **≡** menu.
9. in the export window choose the `Profile Table` then choose `Comma separated values (.csv)`. Make sure that `Include status` is **unchecked!**
10. click on export and wait for the file to be downloaded.

## Script Usage

1. Clone this repository to your local machine.
2. Install the required dependencies by running the following command:
    ```
    pip install -r requirements.txt
    ```
3. Modify the script according to your needs, if necessary.
4. Run the script using the following command:
    ```
    python spooker.py
    ```
5. The script will generate an `import.yaml` and an `export.yaml` next to the script's location.


Alternatively, you can use the compiled executable `EON_SPOOKER.exe` from [releases](https://github.com/Netesfiu/EON_SPOOKER/releases/tag/main). Simply double-click on the executable to run the script.

## importing data to Homeassistant

1. go to development tools>services
2. search for `recorder.import_statistics`
3. choose your utility meter sensor
4. set the source to `recorder`
5. use `kWh` measurement
6. set `has a sum` to `on`
7. under statistics paste the contents of your corresponding yaml file.
8. click on `call_service`
9. done! You now have all your stuff in the corresponding sensor.

### Example yaml :
```yaml
service: recorder.import_statistics
data:
  has_mean: false
  has_sum: true
  statistic_id: sensor.w1000_import
  source: recorder
  unit_of_measurement: kWh
  stats:
    - start: "2021-01-02 00:00:00+02:00"
      sum: 123
    - start: "2021-01-02 01:00:00+02:00"
      sum: 456
    - ...
```

**!!WARNING!!** I Highly recommend making a backup before making any modifications in your sensor's history stats as it can not be undone!



## Contributing

If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.
