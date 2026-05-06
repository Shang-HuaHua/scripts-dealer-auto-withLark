# Workspace Layout

Use this skill only inside the localization workspace whose root contains:

- `app端/`
- `眼镜端/applocalizationtool4anndroid/`

Map the user input to these targets:

- `app端` -> `app端/`
- `眼镜端` -> `眼镜端/applocalizationtool4anndroid/`

For each side:

- Run `reset.command` before reading or editing any Excel file.
- Edit only files under `excel_files/*.xlsx`.
- Run `run.command` after the Excel write succeeds.
- When presenting workbook choices to the user, derive the list dynamically from `excel_files/*.xlsx` instead of hardcoding names in the skill.
- Ignore temporary Excel files such as `.~*.xlsx` and `~$*.xlsx` when building the picker list.

Key facts:

- Excel sheet row 1 is the header row.
- Column `key` is required and must stay unique within the workbook.
- Most workbooks use these language columns:
  `zh`, `en`, `zh-rHK`, `zh-rTW`, `ja`, `de`, `es`, `fr`, `ko`, `vi`, `nl`, `pl`, `it`, `th`
- Some files may include extra columns such as `id`.
- Ignore trailing empty header cells.
