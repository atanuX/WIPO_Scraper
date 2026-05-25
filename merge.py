import os
import pandas as pd

DOWNLOAD_DIR = "wipo_downloads"
OUTPUT_FILE  = "merged_results.xlsx"

all_dfs = []
skipped = []

files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".xlsx")]
print(f"Found {len(files)} files to merge...")

for fname in sorted(files):
    fpath = os.path.join(DOWNLOAD_DIR, fname)
    try:
        xl = pd.ExcelFile(fpath)
        if len(xl.sheet_names) < 2:
            print(f"  [SKIP] Only 1 sheet:  {fname}")
            skipped.append(fname)
            continue
        sheet2_name = xl.sheet_names[1]          # 2nd sheet (index 1)
        df = xl.parse(sheet2_name)

        # Drop the logo column (contains only None/NaN - images are not
        # readable as cell values; removing keeps the sheet clean)
        if "logo" in df.columns:
            df = df.drop(columns=["logo"])

        df["_source_file"] = fname               # track source
        all_dfs.append(df)
        print(f"  [OK]   {fname}  ({len(df)} rows, sheet='{sheet2_name}')")
    except Exception as e:
        print(f"  [ERROR] {fname}: {e}")
        skipped.append(fname)

if not all_dfs:
    print("No data to merge!")
else:
    merged = pd.concat(all_dfs, ignore_index=True)
    merged.to_excel(OUTPUT_FILE, index=False)
    print(f"\nDone! Merged {len(all_dfs)} files -> {len(merged)} total rows")
    print(f"Saved to: {OUTPUT_FILE}")

if skipped:
    print(f"\nSkipped {len(skipped)} files: {skipped}")
