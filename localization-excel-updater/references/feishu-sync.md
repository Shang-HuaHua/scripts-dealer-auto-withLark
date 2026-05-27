# Feishu Sync

This skill can now use Feishu spreadsheets in five ways:

1. Row sync after adding new localization rows locally
2. Row sync after editing existing localization rows locally
3. Bulk download of Feishu spreadsheets into a local folder
4. Bulk pull from Feishu to overwrite local `excel_files/*.xlsx` workbooks
5. Create a brand-new local workbook and matching Feishu spreadsheet

## Current Setup

- `app端` Feishu folder token: `Ngq7f20daljaqydb43ccr4Pjnvm`
- `眼镜端` Feishu folder token: `Fp6MfNpWzl1INxdu6r0c8G3FnmL`

Each local workbook module is matched to the Feishu spreadsheet with the same file name inside the corresponding folder.

Examples:

- `app端 / notification` -> Feishu sheet file named `notification`
- `眼镜端 / launcher` -> Feishu sheet file named `launcher`

## Row Sync Rules

Use this after local `add_rows` writes or local `edit_rows` writes:

- Read the Feishu folder for the selected side.
- Find the spreadsheet whose name exactly matches the local workbook stem, with a case-insensitive fallback.
- Use the first worksheet in that spreadsheet.
- Read the header row from Feishu and use those headers as the authoritative cloud column order.
- Match rows by `key`.
- If the `key` already exists in Feishu, update that row in place.
- If the `key` does not exist, append it after the last non-empty `key` row in Feishu.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/sync_feishu_sheet_rows.py \
  --side app端 \
  --file notification \
  --input /tmp/localization_rows.json
```

## Bulk Download Rules

Use this when the user wants Feishu spreadsheets downloaded locally without changing the source repo:

- Download one side or both sides.
- Optional explicit module list is supported only for a single side.
- Export each Feishu spreadsheet into a standalone `.xlsx` file.
- Default output directory is:
  - `<workspace>/feishu_downloads/<timestamp>/app端/`
  - `<workspace>/feishu_downloads/<timestamp>/眼镜端/`

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  download \
  --scope app端
```

Or:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  download \
  --scope 眼镜端 \
  --file launcher \
  --file media
```

## Bulk Pull Rules

Use this when Feishu is the temporary source of truth and the user wants to write cloud changes back into Git:

- Run the selected side's `reset.command` first.
- Pull one side or both sides.
- Optional explicit module list is supported only for a single side.
- Rebuild the full workbook from Feishu and directly replace the local workbook file under `excel_files/*.xlsx`.
- Overwrite only workbooks that exist both locally and in Feishu.
- When a module is explicitly requested and is missing locally or in Feishu, stop and report the mismatch.
- After overwrite succeeds, run that side's `run.command`.
- If the user selected `全部`, process the two sides sequentially.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  pull \
  --workspace "$PWD" \
  --scope app端
```

Or:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  pull \
  --workspace "$PWD" \
  --scope app端 \
  --file notification \
  --file settings
```

## Create Workbook Rules

Use this when the user wants to add a brand-new workbook on both local and Feishu:

- Run the selected side's `reset.command` first.
- Confirm the workbook name does not already exist locally.
- Confirm the workbook name does not already exist in that side's Feishu folder.
- Create the local workbook under `excel_files/`.
- Create the matching Feishu spreadsheet in the configured folder.
- Write the same standard header row to both.
- After create succeeds, run that side's `run.command`.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  create \
  --workspace "$PWD" \
  --side 眼镜端 \
  --file Widgets
```

## Config

Default config file:

- `feishu_sync_config.json`

The scripts support environment overrides:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_FOLDER_APP`
- `FEISHU_FOLDER_GLASSES`
- `FEISHU_NOTIFICATION_WEBHOOK`

## Success Notification

After the local Excel update, Feishu row sync, and `run.command` push all succeed in `add_rows` mode or `edit_rows` mode, send a Feishu bot webhook message containing:

- side
- file
- each updated `key`
- each row's Chinese `zh` text
- latest Git commit URL
- modified Feishu spreadsheet URL

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/send_feishu_update_webhook.py \
  --side app端 \
  --file notification \
  --input /tmp/localization_rows.json \
  --git-workspace "$PWD"
```

Bulk download and bulk pull do not send the row-level webhook.

## Recommended Workflows

### add_rows

1. Run `reset.command`
2. Update local Excel
3. Sync the same rows to Feishu
4. Only if Feishu sync succeeds, run `run.command`
5. Only if `run.command` push succeeds, show `本次提交: https://...`
6. Only if `run.command` push succeeds, send the Feishu bot webhook notification

### edit_rows

1. Run `reset.command`
2. Resolve the target row by `key` or current Chinese text
3. Update the local workbook row in place
4. Sync the same updated row to Feishu
5. Only if Feishu sync succeeds, run `run.command`
6. Only if `run.command` push succeeds, show `本次提交: https://...`
7. Only if `run.command` push succeeds, send the Feishu bot webhook notification

### download_feishu

1. Resolve side or sides
2. Download Feishu spreadsheets into a local folder
3. Report the output directory and downloaded workbook names

### pull_feishu_to_git

1. Run `reset.command`
2. Pull Feishu spreadsheets and directly replace local `excel_files/*.xlsx` files with the full cloud workbooks
3. Run `run.command`
4. Show `本次提交: https://...`
5. Report which workbooks were overwritten and whether push succeeded

### create_workbook

1. Run `reset.command`
2. Create the new local workbook
3. Create the matching Feishu spreadsheet
4. Write the standard header row to both
5. Run `run.command`
6. Show `本次提交: https://...`
7. Report the local path, Feishu URL, and push result

If Feishu row sync fails, stop before `run.command`.
If bulk pull overwrite fails, stop before `run.command`.
If Git push fails, do not send the row-level webhook notification.
