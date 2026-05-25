import os
import time
import re
import pandas as pd

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException, NoSuchWindowException


# ================= CONFIG =================

INPUT_FILE = "ESPB-input.xlsx"

DOWNLOAD_DIR = os.path.abspath("wipo_downloads")

CHECKPOINT_FILE = "checkpoint.txt"

MAX_RETRIES = 3          # how many times to retry a row after browser crash
DOWNLOAD_TIMEOUT = 120   # seconds to wait for a download before giving up

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ================= CHECKPOINT =================

def load_checkpoint():
    """Load set of already-completed keys from checkpoint file."""
    completed = set()
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                # Strip any suffix like " (no result found)" so the base key
                # is always recognised as done on the next run.
                base_key = raw.replace(" (no result found)", "").strip()
                completed.add(base_key)
        print(f"Checkpoint loaded: {len(completed)} entries already done.")
    else:
        print("No checkpoint file found. Starting fresh.")
    return completed


def save_checkpoint(key):
    """Append a completed key to the checkpoint file."""
    with open(CHECKPOINT_FILE, "a", encoding="utf-8") as f:
        f.write(key + "\n")


def make_checkpoint_key(app_no, brand):
    """Create a unique string key for a row."""
    return f"{app_no}||{brand}"


# ================= BROWSER =================

def start_driver():
    options = uc.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        # Disable SafeBrowsing — prevents "Virus scan failed" blocks
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
        "safebrowsing_for_trusted_sources_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--start-maximized")
    # --- Fully disable SafeBrowsing (required for Chrome 100+) ---
    options.add_argument("--disable-features=SafeBrowsing,SafeBrowsingEnhancedProtection")
    options.add_argument("--safebrowsing-disable-download-protection")
    options.add_argument("--disable-features=InsecureDownloadWarnings")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")

    # undetected_chromedriver handles all anti-bot patching automatically
    # version_main must match your installed Chrome version (145.x)
    _driver = uc.Chrome(options=options, use_subprocess=True, version_main=147)
    _wait = WebDriverWait(_driver, 30)
    return _driver, _wait


def restart_driver(driver):
    """Safely quit the old driver and start a fresh one."""
    try:
        driver.quit()
    except Exception:
        pass
    time.sleep(3)  # brief pause so Chrome fully closes
    return start_driver()


driver, wait = start_driver()


# ================= HELPERS =================

def safe_filename(text):
    if not text:
        return "unknown"
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")

def format_app_no(val):
    if pd.isna(val):
        return ""
    try:
        # Handle cases where it might be a float like 123.0
        if isinstance(val, (float, int)):
            return str(int(float(val)))
        return str(val).strip()
    except:
        return str(val).strip()


def wait_for_download(previous_files, timeout=DOWNLOAD_TIMEOUT):
    """Wait for a new non-temporary file to appear; raises TimeoutError if too long."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(1)
        current_files = set(os.listdir(DOWNLOAD_DIR))
        new_files = current_files - previous_files
        if new_files:
            file = list(new_files)[0]
            if not file.endswith(".crdownload"):
                return file
    raise TimeoutError(f"Download did not complete within {timeout} seconds.")


# ================= INPUT =================

df = pd.read_excel(INPUT_FILE)

total_rows = len(df)
print(f"Total rows: {total_rows}")

completed_keys = load_checkpoint()


# ================= MAIN LOOP =================

for index, row in df.iterrows():
    # 1-based index for display
    current_idx = index + 1

    brand = str(row["Trademark Name"]).strip()

    app_no = format_app_no(row["Application Number"])



    ckpt_key = make_checkpoint_key(app_no, brand)

    # ===== Checkpoint check =====
    if ckpt_key in completed_keys:
        print(f"[{current_idx}/{total_rows}] Skipping (checkpoint): {brand} | {app_no}")
        continue

    new_name = f"{safe_filename(app_no)}_{safe_filename(brand)}.xlsx"
    target_path = os.path.join(DOWNLOAD_DIR, new_name)

    if os.path.exists(target_path):
        if os.path.getsize(target_path) > 100:
            print(f"[{current_idx}/{total_rows}] Skipping: {new_name} (file found)")
            save_checkpoint(ckpt_key)
            completed_keys.add(ckpt_key)
            continue
        else:
            print(f"[{current_idx}/{total_rows}] File exists but is empty, re-processing: {new_name}")

    # ===== Retry loop (handles browser crashes) =====
    success = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\n[{current_idx}/{total_rows}] Processing: {brand} | {app_no}"
                  + (f" (attempt {attempt}/{MAX_RETRIES})" if attempt > 1 else ""))

            driver.get("https://branddb.wipo.int/en/similarname")

            time.sleep(10)
            brand_box = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[normalize-space()='Brand name']/following::input[1] | //label[normalize-space()='Brand name']/following::input[1]")
                )
            )

            brand_box.clear()
            brand_box.send_keys(brand)


            # ===== Application number =====

            app_box = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(normalize-space(),'Application') and contains(normalize-space(),'Registration')]/following::input[1] | //label[contains(.,'Application')]/following::input[1]")
                )
            )

            app_box.clear()
            app_box.send_keys(app_no)




            # ===== Search =====

            search_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='Search']]")
                )
            )

            search_btn.click()

            time.sleep(6)


            # ===== Check for no results =====

            no_result_indicators = [
                "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no results')]",
                "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result found')]",
                "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'0 results')]",
            ]

            no_result_found = False
            for xpath in no_result_indicators:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if any(el.is_displayed() for el in elements):
                        no_result_found = True
                        break
                except:
                    pass

            if no_result_found:
                no_result_key = ckpt_key + " (no result found)"
                save_checkpoint(no_result_key)
                completed_keys.add(ckpt_key)  # mark as done so it won't retry
                print(f"[{current_idx}/{total_rows}] No results found for: {brand} | {app_no} — logged to checkpoint")
                success = True
                break


            # ===== Download results =====

            download_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(),'Download results')]")
                )
            )

            driver.execute_script("arguments[0].click();", download_btn)

            time.sleep(2)


            # ===== Excel option =====

            excel_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//i[@icon='download']/following-sibling::span[contains(text(),'Excel')]")
                )
            )

            before_files = set(os.listdir(DOWNLOAD_DIR))

            driver.execute_script("arguments[0].click();", excel_btn)


            # ===== Wait for download =====

            downloaded = wait_for_download(before_files)


            # ===== Rename file =====

            os.rename(
                os.path.join(DOWNLOAD_DIR, downloaded),
                os.path.join(DOWNLOAD_DIR, new_name)
            )

            save_checkpoint(ckpt_key)
            completed_keys.add(ckpt_key)
            print(f"[{current_idx}/{total_rows}] Saved & checkpointed: {new_name}")
            success = True
            break  # done — exit retry loop

        except (InvalidSessionIdException, WebDriverException, NoSuchWindowException) as e:
            print(f"[{current_idx}/{total_rows}] Browser session lost or crashed: {e}")
            if attempt < MAX_RETRIES:
                print(f"Restarting browser and retrying row (attempt {attempt + 1}/{MAX_RETRIES})...")
                driver, wait = restart_driver(driver)
            else:
                print(f"[{current_idx}/{total_rows}] Max retries reached. Skipping for now (will retry on next run).")

        except TimeoutError as e:
            print(f"[{current_idx}/{total_rows}] Download timed out: {e}")
            if attempt < MAX_RETRIES:
                print(f"Retrying row (attempt {attempt + 1}/{MAX_RETRIES})...")
                driver, wait = restart_driver(driver)
            else:
                print(f"[{current_idx}/{total_rows}] Max retries reached. Skipping for now.")

        except Exception as e:
            print(f"[{current_idx}/{total_rows}] Error processing {brand} | {app_no}: {e}")
            break  # non-browser errors: skip without retrying

    if not success:
        print(f"[{current_idx}/{total_rows}] Row not completed — will be retried on next run (not checkpointed).")


# ================= FINISH =================

driver.quit()

print("\nAll downloads completed.")