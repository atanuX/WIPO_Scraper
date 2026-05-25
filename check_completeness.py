import os
import re

# Parse checkpoint file
checkpoint_ids = {}
with open(r'c:\Users\asus\Downloads\wipo-ESPB\checkpoint.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split('||', 1)
        if len(parts) == 2:
            id_val = parts[0].strip()
            name_val = parts[1].strip()
            if id_val == '' or id_val == 'Grand Total':
                continue
            is_no_result = '(no result found)' in name_val
            checkpoint_ids[id_val] = {'name': name_val, 'no_result': is_no_result}

print(f'Total checkpoint entries: {len(checkpoint_ids)}')

# Collect entries that should have files (not 'no result found')
should_have_file = {k: v for k, v in checkpoint_ids.items() if not v['no_result']}
no_result_entries = {k: v for k, v in checkpoint_ids.items() if v['no_result']}

print(f'Entries that should have files: {len(should_have_file)}')
print(f'Entries marked no result found: {len(no_result_entries)}')

# Get downloaded files
download_dir = r'c:\Users\asus\Downloads\wipo-ESPB\wipo_downloads'
downloaded_files = os.listdir(download_dir)

# Extract IDs from filenames (format: ID_NAME.xlsx)
downloaded_ids = set()
extra_files = []
for f in downloaded_files:
    if f.endswith('.xlsx'):
        match = re.match(r'^(\d+)_', f)
        if match:
            downloaded_ids.add(match.group(1))
        else:
            extra_files.append(f)

print(f'\nTotal downloaded files: {len(downloaded_files)}')
print(f'Downloaded with valid IDs: {len(downloaded_ids)}')
if extra_files:
    print(f'Files without standard ID format: {extra_files}')

# Find missing: should have file but not downloaded
missing = {k: v for k, v in should_have_file.items() if k not in downloaded_ids}
print(f'\n=== MISSING FILES ({len(missing)}) ===')
for id_val, info in sorted(missing.items()):
    print(f'  ID: {id_val} | Name: {info["name"]}')

# Find extra: downloaded but not in checkpoint at all
all_checkpoint_ids = set(checkpoint_ids.keys())
extra_downloaded = downloaded_ids - all_checkpoint_ids
if extra_downloaded:
    print(f'\n=== EXTRA DOWNLOADS not in checkpoint: {len(extra_downloaded)} ===')
    for id_val in sorted(extra_downloaded):
        print(f'  ID: {id_val}')

# No-result entries that somehow have files
no_result_but_has_file = {k: v for k, v in no_result_entries.items() if k in downloaded_ids}
if no_result_but_has_file:
    print(f'\n=== NO-RESULT entries that HAVE a file: {len(no_result_but_has_file)} ===')
    for id_val, info in sorted(no_result_but_has_file.items()):
        print(f'  ID: {id_val} | Name: {info["name"]}')

print('\n=== SUMMARY ===')
print(f'Checkpoint total entries: {len(checkpoint_ids)}')
print(f'  - Should have file: {len(should_have_file)}')
print(f'  - No result found (skip): {len(no_result_entries)}')
print(f'Total downloaded (xlsx): {len(downloaded_ids)}')
print(f'Missing downloads: {len(missing)}')
if len(missing) == 0:
    print('All expected files are downloaded!')
