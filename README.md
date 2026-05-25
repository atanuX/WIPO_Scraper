# WIPO Scraper

A robust and resilient Python-based web scraper built to extract trademark data from the WIPO (World Intellectual Property Organization) Brand Database.

## Overview

This tool automates the process of querying the [WIPO Global Brand Database](https://branddb.wipo.int/en/similarname) using an input list of trademark names and application numbers. It handles browser automation with `undetected_chromedriver` to bypass bot protections, downloads the resulting Excel reports, and merges them into a single consolidated output file.

## Features

* **Anti-Bot Evasion**: Utilizes `undetected_chromedriver` to bypass standard bot detection and download blocks.
* **Resilient Execution**: Implements a robust checkpointing system (`checkpoint.txt`). If the browser crashes, encounters an error, or the execution is manually stopped, the script will resume exactly where it left off.
* **Automatic Error Handling & Retries**: Automatically retries failed rows due to timeouts or browser crashes.
* **Empty Result Handling**: Correctly identifies when a search yields "0 results" and logs it without failing.
* **Data Consolidation**: Includes a `merge.py` utility that processes the downloaded individual Excel files, cleans them (removes unreadable logo columns), and merges them into a single `merged_results.xlsx` file.

## Prerequisites

* Python 3.x
* Google Chrome browser installed (the script requires `version_main` in `uc.Chrome()` to match your installed Chrome version).

## Setup & Dependencies

Install the required Python packages:

```bash
pip install pandas openpyxl undetected-chromedriver selenium
```

## Usage

### 1. Prepare Input Data
Ensure your input file is named `ESPB-input.xlsx` and is located in the root directory. It must contain the following columns:
* `Trademark Name`
* `Application Number`

### 2. Run the Scraper
Execute the main scraping script:
```bash
python main.py
```
The script will process each row, perform the search on the WIPO database, and download the results as `.xlsx` files into the `wipo_downloads/` directory. Progress is tracked in `checkpoint.txt`.

### 3. Merge Results
Once the scraper has finished (or if you want to merge currently downloaded files), run the merge script:
```bash
python merge.py
```
This will generate a `merged_results.xlsx` file containing all the extracted data.

## Important Notes

* **Chrome Version**: The script is currently hardcoded for a specific Chrome version (`version_main=147` in `main.py`). Update this value to match your local Chrome version.
* **Safe Browsing**: The script disables Chrome's SafeBrowsing features to prevent files from being blocked during automated downloads. Use with trusted sources only.
