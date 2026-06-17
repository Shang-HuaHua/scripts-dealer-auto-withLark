---
name: localization-excel-updater
description: Update Rokid localization workbooks, manage Feishu workbook sync, and publish the skill itself to a target Git repository.
---

# Localization Excel Updater

Use this skill as a strict workflow. Do not skip the reset step before any local overwrite. Do not edit `.xlsx` files manually.

Read [workspace-layout.md](./references/workspace-layout.md) once at the start.
Read [feishu-sync.md](./references/feishu-sync.md) when syncing cloud docs, bulk-downloading Feishu spreadsheets, pulling Feishu spreadsheets back to local, or sending update notifications.
If the user asks how to install, share, or first-use this skill, read [user-onboarding.md](./references/user-onboarding.md).

## Supported Modes

This skill now supports seven operation modes.

1. Add rows:
   - generate new keys
   - fill translations
   - append the rows to a local workbook
   - sync the same rows to Feishu
   - run `run.command`
   - push Git
   - send the success webhook
2. Bulk download:
   - download Feishu spreadsheets in bulk into a local folder
   - do not touch local source workbooks
   - do not run Git
3. Edit existing rows:
   - locate an existing row by `key` or by current Chinese text
   - keep the existing `key`
   - replace the requested text fields
   - regenerate translations for the workbook's existing language columns
   - update the local workbook and matching Feishu spreadsheet in place
   - run `run.command`
   - push Git unless the user explicitly says not to submit
   - do not send the success webhook
4. Pull from Feishu and push Git:
   - reset the selected side first
   - pull Feishu spreadsheets
   - download the full workbook content for each selected Excel file
   - directly replace the matching local `excel_files/*.xlsx` file with the freshly pulled workbook
   - run `run.command`
   - push Git
5. Create workbook:
   - ask for the selected fixed side and workbook name
   - validate that the workbook name uses English letters, with optional underscores between words
   - validate that the workbook name does not conflict with any existing Excel name on the selected fixed side
   - derive the standard header row from the selected fixed side
   - create a new local workbook under that side's standard `excel_files/` path
   - create the matching Feishu spreadsheet, run `run.command`, and push Git
6. Publish the skill repo:
   - export the current `localization-excel-updater` skill folder
   - optionally include the Chinese update-and-usage document
   - copy the latest skill content into a provided local Git repository
   - commit and push the repository
7. Find existing text:
   - search existing workbooks for a provided Chinese text
   - return the matched side, workbook, local workbook link, `key`, and row number
   - do not modify any workbook
   - do not run `run.command`
   - do not run Git

## Operation Detection

Resolve the user request into one of these intents:

- If the user gives Chinese UI fields and wants new localization rows, use `add_rows`.
- If the user wants to modify an existing localization row while keeping the same `key`, use `edit_rows`.
- If the user asks to download Feishu cloud workbooks locally, use `download_feishu`.
- If the user asks to pull Feishu cloud workbooks back to local and upload Git, use `pull_feishu_to_git`.
- If the user asks to add a brand-new workbook or table on both local and Feishu, use `create_workbook`.
- If the user asks to update, export, or publish this skill itself into a provided Git repository, use `publish_skill_repo`.
- If the user asks where a Chinese text already exists, use `find_text`.

Examples:

- `字段：登录成功\n登录失败` -> `add_rows`
- `把 key=not_connected 改成 未连接设备` -> `edit_rows`
- `把 home 里“未连接”改成“未连接设备”，key 不变` -> `edit_rows`
- `下载飞书 app端` -> `download_feishu`
- `把飞书眼镜端覆盖到本地并上传 git` -> `pull_feishu_to_git`
- `从飞书回拉 app端 notification 和 settings，再推 git` -> `pull_feishu_to_git`
- `眼镜端新增一个 Widgets 表格` -> `create_workbook`
- `把这个 skill 更新到我给的 Git 仓库` -> `publish_skill_repo`
- `把 localization-excel-updater 导出并推到提供的 GitHub 仓库` -> `publish_skill_repo`
- `帮我找一下“已复制到剪切板”在哪个表格` -> `find_text`

## Required Input By Mode

### add_rows

Collect or infer:

- Side: `app端` or `眼镜端`
- File: workbook name such as `settings`, `basic`, `launcher`
- One or more Chinese UI strings

If side or file is missing, switch to guided selection mode instead of asking an open-ended question.

### edit_rows

Collect or infer:

- Side: `app端` or `眼镜端`
- File: workbook name such as `settings`, `basic`, `launcher`
- One or more existing row targets:
  - explicit `key`, or
  - current Chinese text from the `zh` column
- The replacement Chinese text

If the user gives Chinese text instead of `key`, resolve the matching row from the workbook before editing.
If the same Chinese text matches multiple rows in the workbook, stop and ask the user to provide the key.

### download_feishu

Collect or infer:

- Scope:
  - `app端`
  - `眼镜端`
  - `全部`
- Optional file list when the scope is a single side

If the user gives only a side, download all Feishu spreadsheets for that side.
If the user gives `全部`, download both sides.
If the user gives explicit file names, keep the scope to a single side.

### pull_feishu_to_git

Collect or infer:

- Scope:
  - `app端`
  - `眼镜端`
  - `全部`
- Optional file list when the scope is a single side

If the user gives only a side, pull all Feishu spreadsheets for that side and overwrite all matching local workbooks for that side.
If the user gives `全部`, process `app端` and `眼镜端` sequentially.
If the user gives explicit file names, keep the scope to a single side.

### create_workbook

Collect or infer:

- Side: `app端` or `眼镜端`
- File: new workbook name such as `Widgets`

This mode creates one brand-new workbook at a time.
Do not guess a file name if the user did not provide one.
Workbook names must use English letters only, with optional underscores used only as word separators.
Workbook names must not contain spaces or Chinese characters.
Workbook names must not duplicate any existing Excel module name on the selected side.

### publish_skill_repo

Collect or infer:

- Local target repository path
- Optional remote URL if the local repo is not prepared yet
- Whether to include the Chinese update-and-usage document
- Optional commit message

Prefer a prepared local repo path when available.
If the user gives only a remote URL, create or reuse a local export repo first, then bind that remote.

### find_text

Collect or infer:

- Search text from the workbook `zh` column
- Optional side:
  - `app端`
  - `眼镜端`
  - omitted means search both sides

If the side is omitted, search both sides before replying.
Prefer exact `zh` matches first. If there is no exact match, report that and optionally include unique substring matches when they are helpful.

## Preferred Input Formats

### add_rows

Guided selection remains the default. Direct input still works when the user already knows the target.

User can start with fields only:

```text
字段：
登录成功
登录失败
网络异常，请稍后重试
```

Then guide them in two steps.

Step 1:

```text
请选择端：
1. app端
2. 眼镜端
```

Step 2:

After the user picks a side, read that side's local `excel_files/*.xlsx` dynamically with [list_workbooks.py](./scripts/list_workbooks.py), then show only that side's current file list and allow either the number or the file name.

Direct templates:

```text
端：app端
文件：settings
字段：
登录成功
登录失败
```

```text
app端 settings：
登录成功；登录失败
```

### edit_rows

Prefer these forms:

```text
端：app端
文件：home
修改：
key：not_connected
改为：未连接设备
```

```text
端：app端
文件：home
修改：
原文：未连接
改为：未连接设备
```

```text
app端 home：
把“未连接”改成“未连接设备”，key 不变
```

### download_feishu

Prefer these forms:

```text
下载飞书 app端
```

```text
下载飞书 眼镜端
```

```text
下载飞书 全部
```

```text
下载飞书
范围：app端
文件：
notification
settings
```

### pull_feishu_to_git

Prefer these forms:

```text
从飞书回拉 app端 并上传 git
```

```text
从飞书回拉 眼镜端 并推送 git
```

```text
从飞书回拉 全部，覆盖本地后上传 git
```

```text
从飞书回拉
范围：app端
文件：
notification
settings
操作：覆盖本地并上传 git
```

### create_workbook

Prefer these forms:

```text
眼镜端新增一个 Widgets 表格
```

```text
给 app端 新建一个 workbook：sdk_new
```

```text
创建表格
端：眼镜端
文件：Widgets
```

### publish_skill_repo

Prefer these forms:

```text
把这个 skill 更新到我给的 Git 仓库
本地仓库：/path/to/repo
```

```text
把 Localization Excel Updater 导出并推到这个仓库：
git@github.com:xxx/yyy.git
```

```text
发布 skill
本地仓库：/path/to/repo
提交说明：update skill workflow
```

### find_text

Prefer these forms:

```text
用 Localization Excel Updater
帮我找一下这个文案 “已复制到剪切板” 在哪个表格
```

```text
用 Localization Excel Updater
查找文案
内容：已复制到剪切板
```

```text
用 Localization Excel Updater
端：app端
查找文案：已复制到剪切板
```

## Parsing Rules

- Accept side aliases only as `app端` and `眼镜端` when replying to the user.
- Accept scope aliases `全部` and `两端全部` as the two-side bulk target.
- Accept file names with or without `.xlsx`, but normalize to the workbook stem.
- Treat each line under `字段：` as one field for `add_rows`.
- In inline text, split multiple UI fields on `、`, `，`, `；`, `;`, or line breaks.
- Ignore surrounding quotes such as `“登录成功”`.
- Remove empty entries after splitting.
- When the request already contains exactly one mode, one side or scope, and the needed file data for that mode, proceed without asking.
- For `edit_rows`, prefer matching by explicit `key` when the user gives one.
- For `edit_rows`, if the user gives only current Chinese text, look for an exact `zh` match first. Only fall back to a unique substring match if the exact match is missing.
- For `download_feishu` and `pull_feishu_to_git`, do not ask the user to repeat the whole request if only the scope is missing.
- If the user requests bulk work for `全部` and also gives a file list, ask them to split it into one side at a time instead of guessing across both sides.
- For `create_workbook`, require exactly one side and one new workbook name.
- For `create_workbook`, stop if the workbook already exists locally or in Feishu instead of silently reusing it.
- For `create_workbook`, validate the workbook name with `^[A-Za-z]+(?:_[A-Za-z]+)*$`. Reject spaces, Chinese characters, digits, hyphens, leading underscores, trailing underscores, and consecutive underscores.
- For `create_workbook`, compare workbook names case-insensitively against the selected side's existing Excel names and reject duplicates.
- For `edit_rows`, keep the original `key` unchanged unless the user explicitly asks to rename the key. Renaming keys is out of scope for this skill.
- For `publish_skill_repo`, treat the current skill directory as the source of truth and do not edit files directly inside the target repo copy before syncing.
- For `find_text`, search the `zh` column only unless the user explicitly asks for another language column.
- For `find_text`, ignore temporary Excel files such as `.~launcher.xlsx` and `~$foo.xlsx`.
- For `find_text`, if there are multiple matches, list every match instead of guessing which one the user wants.

## Guided Selection

Default to this flow only for `add_rows`, `edit_rows`, or when a bulk request is missing the side/scope.

### Side Picker

Reply with:

```text
请选择端：
1. app端
2. 眼镜端
```

Accept:

- `1` -> `app端`
- `2` -> `眼镜端`

### Bulk Scope Picker

For `download_feishu` and `pull_feishu_to_git`, if the side/scope is missing, reply with:

```text
请选择范围：
1. app端全部
2. 眼镜端全部
3. 两端全部
```

Accept:

- `1` -> `app端`
- `2` -> `眼镜端`
- `3` -> `全部`

### File Picker For add_rows / edit_rows

Do not hardcode workbook names in this skill.

Always read the current local workbook list from the selected side:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/list_workbooks.py \
  --workspace "$PWD" \
  --side 眼镜端
```

Or use JSON if you need the raw module array:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/list_workbooks.py \
  --workspace "$PWD" \
  --side app端 \
  --json
```

Rules:

- Ignore temporary Excel files such as `.~launcher.xlsx` and `~$foo.xlsx`.
- Show the numbered list returned by the script.
- Accept either the displayed number or the exact file name.
- Because the picker is dynamic, newly added local workbooks such as `Widgets.xlsx` will appear automatically without editing this skill again.

### Row Matching For edit_rows

When the user does not provide a `key`:

1. Read the target workbook.
2. Try to find an exact `zh` match for the provided current text.
3. If there is exactly one exact match, use that row's `key`.
4. If there is no exact match, try a unique substring match in `zh`.
5. If there are multiple matches, stop and ask the user for the exact `key`.

### Text Matching For find_text

1. Read the selected side's local workbooks under `excel_files/*.xlsx`.
2. Ignore temporary files such as `.~*.xlsx` and `~$*.xlsx`.
3. Search exact matches in the `zh` column first.
4. If there are no exact matches, optionally collect substring matches that contain the query text.
5. Return every exact match. Only mention substring matches when exact matches are missing.

## Workflow: find_text

1. Resolve the target side. If omitted, search both `app端` and `眼镜端`.
2. Read each selected workbook locally. Do not run `reset.command`.
3. Search the `zh` column for the requested text, preferring exact matches.
4. Return each match with:
   - side
   - workbook file name
   - local workbook file link
   - `key`
   - row number
5. If no exact match is found, clearly say so and optionally include any useful substring matches.
6. Do not write any workbook, sync Feishu, run `run.command`, or run Git.

## Workflow: add_rows

1. Resolve the target side and workbook path from the current workspace.
2. Run the matching `reset.command` and wait for it to finish successfully before reading the workbook.
3. Inspect the workbook header row and existing keys.
4. For each Chinese UI string, generate:
   - one new `key`
   - translations for every non-empty language column in the workbook
   - values for non-language columns only when the workbook already uses them and the correct value is clear; otherwise leave them empty
5. Append the new rows with [append_excel_rows.py](./scripts/append_excel_rows.py).
6. Sync the same rows into the matching Feishu spreadsheet with [sync_feishu_sheet_rows.py](./scripts/sync_feishu_sheet_rows.py).
7. Only if the Feishu sync succeeds, run the matching `run.command` and wait for the push to complete.
8. Only if the push succeeds, send the success webhook with [send_feishu_update_webhook.py](./scripts/send_feishu_update_webhook.py).
9. Run [build_gitlab_commit_link.py](./scripts/build_gitlab_commit_link.py) and display the GitLab links to the user.
10. Report the added keys, target workbook, Feishu sync result, webhook result, and whether the push succeeded.

## Workflow: edit_rows

1. Resolve the target side and workbook path from the current workspace.
2. Run the matching `reset.command` and wait for it to finish successfully before reading the workbook.
3. Resolve each target row by explicit `key` or by current `zh` text.
4. Inspect nearby workbook rows and preserve the existing terminology and style.
5. Keep the original `key` and replace the requested text fields.
6. Regenerate translations for every existing language column in that workbook row.
7. Update the local workbook in place with [update_excel_rows.py](./scripts/update_excel_rows.py).
8. Sync the same updated rows into the matching Feishu spreadsheet with [sync_feishu_sheet_rows.py](./scripts/sync_feishu_sheet_rows.py).
9. Only if the Feishu sync succeeds, run the matching `run.command` and wait for the push to complete, unless the user explicitly said not to submit.
10. Do not send the success webhook for edit-only changes.
11. Run [build_gitlab_commit_link.py](./scripts/build_gitlab_commit_link.py) and display the GitLab links to the user when a push occurred.
12. Report the updated keys, target workbook, Feishu sync result, whether the push succeeded, and that the Feishu group notification was intentionally skipped.

## Workflow: download_feishu

1. Resolve the bulk scope:
   - `app端`
   - `眼镜端`
   - `全部`
2. If the user gave an explicit file list, keep the scope to a single side.
3. Download the requested Feishu spreadsheets with [manage_feishu_workbooks.py](./scripts/manage_feishu_workbooks.py) in `download` mode.
4. Save the exported `.xlsx` files under a local download directory.
5. Report the download directory, downloaded workbook count, and the workbook names.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  download \
  --scope app端
```

Or for explicit modules:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  download \
  --scope app端 \
  --file notification \
  --file settings
```

Rules:

- Download mode does not edit the workspace source workbooks.
- Download mode does not run `reset.command`.
- Download mode does not run `run.command`.
- Download mode does not push Git.

## Workflow: pull_feishu_to_git

1. Resolve the bulk scope:
   - `app端`
   - `眼镜端`
   - `全部`
2. If the user gave explicit file names, keep the scope to a single side.
3. For each selected side, run that side's `reset.command` before any overwrite.
4. Pull the requested Feishu spreadsheets with [manage_feishu_workbooks.py](./scripts/manage_feishu_workbooks.py) in `pull` mode.
5. For each selected workbook, rebuild the full cloud workbook and directly replace the matching local `excel_files/*.xlsx` file.
6. Run that side's `run.command`.
7. Confirm commit and push success for that side.
8. Run [build_gitlab_commit_link.py](./scripts/build_gitlab_commit_link.py) for that side and display the GitLab links to the user.
9. If the scope is `全部`, process the second side only after the first side finishes successfully.
10. Report which workbooks were overwritten and whether each selected side pushed successfully.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  pull \
  --workspace "$PWD" \
  --scope 眼镜端
```

Or for explicit modules:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  pull \
  --workspace "$PWD" \
  --scope app端 \
  --file notification \
  --file settings
```

Rules:

- Always run `reset.command` before calling the pull mode for that side.
- Pull mode replaces matching local workbooks directly under `excel_files/` with the full workbook pulled from Feishu.
- Pull mode must not do an in-place row or cell patch on the existing local Excel file. This avoids leaving behind stale rows that were already deleted in Feishu.
- Pull mode updates only workbooks that exist locally and in Feishu.
- If the user explicitly names a workbook and it is missing locally or in Feishu, stop and report the mismatch.
- For `全部`, run the two sides sequentially, not in parallel.
- Bulk pull mode does not send the row-level success webhook, because it is not a single added-row batch.

## Workflow: create_workbook

1. Resolve the selected fixed side and new workbook name.
2. Run the matching `reset.command` and wait for it to finish successfully.
3. Validate that the workbook name uses only English letters, with optional underscores between words.
4. Confirm the workbook name does not duplicate any existing Excel name on the selected side.
5. Derive the header row from the selected side's existing Excel files.
6. Create the new local workbook under that side's standard `excel_files/` path.
7. Create the matching Feishu spreadsheet and write the same header row to row 1.
8. Run the matching `run.command`.
9. Confirm commit and push success.
10. Send the success webhook with [send_feishu_update_webhook.py](./scripts/send_feishu_update_webhook.py) after the push succeeds, because a new workbook was created.
11. Run [build_gitlab_commit_link.py](./scripts/build_gitlab_commit_link.py) and display the GitLab links to the user.
12. Report the new local path, the selected header side, the Feishu spreadsheet URL, webhook result when applicable, and push result.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/manage_feishu_workbooks.py \
  create \
  --workspace "$PWD" \
  --side 眼镜端 \
  --file Widgets
```

Rules:

- Create mode supports only one side and one workbook at a time.
- Create mode derives the standard header row from existing workbooks on the selected side instead of hardcoding it in the skill.
- Create mode always creates the local workbook under the selected side's standard `excel_files/` directory.
- Create mode validates workbook names with English letters and optional underscores only.
- Create mode rejects names that conflict, case-insensitively, with any existing Excel file on the selected side.
- Create mode is a hard stop if the workbook already exists locally or in Feishu.
- Create mode sends a webhook whenever a new workbook is created and pushed. If rows were added to the new workbook before upload, include those row details; if the workbook only has headers, notify that the new workbook was created.

## Workflow: publish_skill_repo

1. Resolve the source skill directory as the current installed `localization-excel-updater` folder.
2. Resolve the target local Git repository path.
3. If the user provided only a remote URL, prepare a local export repository first and bind the remote.
4. Copy the full skill folder into the target repo with [publish_skill_repo.py](./scripts/publish_skill_repo.py).
5. Include the Chinese update-and-usage document when the repository is intended for sharing or backup.
6. Run `git status` and verify the exported files are present.
7. Stage the updated files.
8. Create a commit with either the user-provided message or a concise default message.
9. Push the target repository to its configured remote.
10. Report the local repo path, pushed branch, and remote URL.
11. After every successful skill-repo push, provide a short `本次提交描述（中文版）` section that summarizes the actual update points in natural Chinese.

Use:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/publish_skill_repo.py \
  --skill-dir /Users/rokid/.codex/skills/localization-excel-updater \
  --repo-dir /path/to/local/repo \
  --target-folder localization-excel-updater \
  --doc /path/to/更新说明与用法（中文）.md
```

Rules:

- Publish mode updates the skill files inside a Git repo; it does not modify Feishu workbooks.
- Publish mode should preserve the target repo's `.git` directory and remote settings.
- If `git push` fails, report that the repo content and local commit were updated but remote push did not succeed.
- When replying after a successful skill-repo update, do not show only the commit hash. Always include a Chinese explanation of what changed in this submission, based on the real update points.

## Key Rules

- Keep keys lowercase snake_case.
- Use only ASCII letters, digits, and underscores.
- Make the key short, readable, and semantically tied to the Chinese UI text and file context.
- Do not mechanically prefix keys with the workbook name or side name. The downstream codebase already composes table context with the key, so default to the shortest clear key that fits the row meaning.
- Add a workbook-specific prefix only when it is truly needed to avoid a collision inside the same workbook or when the user explicitly requests that naming style.
- Never reuse a key already present in the workbook.
- When a candidate key collides, keep the base meaning and add a short suffix instead of changing the meaning.
- Treat uniqueness as workbook-scoped.

## Translation Rules

- Fill every language column that exists in the workbook.
- Treat any workbook header that is a language code as a required translation column, including columns such as `id` when they represent Indonesian.
- Translate strictly by the workbook's language codes and fill the matching value for each existing language column.
- Treat the Chinese source text as software UI copy. Translations must be precise, complete, and as short as possible while preserving the full original meaning.
- Do not change the meaning of the Chinese source. Do not add explanations, extra nuance, or product behavior that is not present in the source text.
- Before generating new translations, inspect nearby rows in the target workbook and keep terminology, tone, and approximate length aligned with the existing file.
- Keep UI copy natural and ready for direct use in the interface, not as explanatory prose.
- Preserve placeholders, punctuation, line breaks, brand names, product names, and formatting markers.
- If the user types visible escape sequences such as `\n`, `\t`, `\"`, or `\\` in the source text, keep those characters literally in the workbook cells. Do not decode them into actual newlines, tabs, or other escaped characters unless the user explicitly asks for that conversion.
- Treat this as a one-layer literal write rule. Example: if the user inputs `第一行\n第二行`, the final cell value must contain exactly `\n` between the two phrases. Do not turn it into a real line break, and do not over-escape it into `\\n`.
- Execution safeguard: when building temporary row JSON for any text that may contain visible escape sequences, do not embed the user text directly inside Python string literals or shell JSON snippets. Instead, write the exact source text to a UTF-8 temp file first and reference it from the row JSON with `@file:/absolute/path.txt`. The Excel update and Feishu sync scripts now resolve `@file:` values by reading the file content verbatim.
- Between Chinese characters and Latin letters/numbers, insert a half-width space for readability. Apply this to all language columns. Examples: `登录API接口` → `登录 API 接口`, `蓝牙BLE` → `蓝牙 BLE`, `WiFi6` → `WiFi 6`, `iPhone16` → `iPhone 16`. Brand names composed entirely of Latin letters (e.g. `Rokid`, `WiFi`) do not need internal spacing; only add spaces at the boundary between CJK and Latin characters.
- Keep `zh` aligned with the user-provided Chinese text unless the text clearly contains an obvious typo or formatting issue. The spacing rule above also applies when writing back the `zh` column: auto-insert half-width spaces between Chinese and Latin/number boundaries even if the user's original input did not include them.
- Keep repeated concepts translated consistently within the current batch, within the current workbook, and with any existing workbook terminology.
- Product-name override: when the product term `看一下支付` appears, keep `zh`, `zh-rHK`, and `zh-rTW` translated in their Chinese locales (`看一下支付` / `看一下支付` / `看一下支付` inside the surrounding sentence). For all non-Chinese language columns, use the brand text `Alipay look` inside the surrounding sentence.
- For titles, buttons, switches, and enum values, prefer short UI-style wording.
- For description fields, allow a complete sentence, but keep it concise and consistent with the paired title field.
- For enum-like values such as `常开`, `关闭`, and `智能`, choose the natural system-setting wording in each language.
- `zh-rHK` must use Hong Kong Traditional Chinese wording and display style. Prefer Hong Kong UI vocabulary and phrasing, and do not fall back to Simplified Chinese.
- `zh-rTW` must use Taiwan Traditional Chinese wording and display style. Prefer Taiwan UI vocabulary and phrasing, and do not fall back to Simplified Chinese.
- For both `zh-rHK` and `zh-rTW`, do not output Simplified Chinese characters. If a generated phrase contains any Simplified Chinese wording or Mainland-specific phrasing, rewrite it before writing the workbook.
- Do not do a mechanical simplified-to-traditional character swap if a more natural locale-specific phrase is available.
- Do not leave an existing language column blank unless the user explicitly asks for that or the source text is genuinely not translatable without clarification.
- If a translation is uncertain, choose the safest natural UI wording instead of leaving the cell blank.
- **Capitalization for Latin-script languages** (en, de, es, fr, nl, pl, it, pt, id, vi): Use sentence case — only the first letter of the entire string is capitalized, all other letters are lowercase. Examples: `Data Sync` → `Data sync`, `Glasses Wi-Fi Cannot Be Turned Off` → `Glasses Wi-Fi cannot be turned off`.
- For `en`, treat this as a hard rule by default: only the first letter of the full string may be capitalized, and all other non-brand words must stay lowercase unless the user explicitly requests otherwise.
- Preserve required capitalization only for product names, brand names, abbreviations, and user-requested casing overrides.

## Excel Write Rules

- Use the append script for every `add_rows` workbook edit:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/append_excel_rows.py \
  --workspace "$PWD" \
  --side app \
  --file settings \
  --input /tmp/localization_rows.json
```

- The JSON input must be a list of row objects keyed by workbook header names.
- The append script rejects duplicate keys against both the workbook and the current batch.
- The append script writes directly after the last non-empty `key` row, not after `max_row`.

- Use the update script for every `edit_rows` workbook edit:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/update_excel_rows.py \
  --workspace "$PWD" \
  --side app \
  --file settings \
  --input /tmp/localization_rows.json
```

- The update JSON input must be a list of row objects that each include an existing `key`.
- The update script keeps all unspecified columns unchanged.
- The update script fails if any provided `key` does not already exist in the workbook.

## Feishu Sync Rules

- Use the row-sync script after a successful local Excel append in `add_rows` mode and after a successful local row update in `edit_rows` mode:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/sync_feishu_sheet_rows.py \
  --side app端 \
  --file notification \
  --input /tmp/localization_rows.json
```

- Match the Feishu spreadsheet by file name inside the configured side folder.
- Match Feishu rows by `key`, not by row number.
- If the `key` exists in Feishu, update that row in place.
- If the `key` does not exist, append it after the last non-empty Feishu `key` row.
- Treat Feishu row-sync failure as a hard stop for `add_rows` and `edit_rows`. Do not continue to `run.command` if the cloud sync failed.

## Webhook Rules

- After a successful `add_rows` workflow that creates new keys, send a Feishu bot webhook notification with [send_feishu_update_webhook.py](./scripts/send_feishu_update_webhook.py). Also send it after a successful `create_workbook` push when a new workbook was created, with or without rows added in the same workflow:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/send_feishu_update_webhook.py \
  --side app端 \
  --file notification \
  --input /tmp/localization_rows.json \
  --git-workspace <workspace_path>
```

- Send the webhook only after local Excel update, Feishu row sync when applicable, and Git push all succeed.
- The webhook message must include the selected side, file, each newly added row's `key` plus Chinese `zh` text when rows were added, the latest Git commit URL, and the updated Feishu document URL.
- Do not send the webhook if Feishu sync failed or if `run.command` push failed.
- Do not send the row-level webhook for `edit_rows`, `download_feishu`, or `pull_feishu_to_git`.
- If the user asks to fix keys or translations right after an `add_rows` push, process it as `edit_rows`: sync Feishu, run `run.command`, push Git unless explicitly told not to submit, and skip the Feishu group webhook.

## GitLab Link Display

After every successful Git push in `add_rows`, `pull_feishu_to_git`, or `create_workbook` mode, the AI must run [build_gitlab_commit_link.py](./scripts/build_gitlab_commit_link.py) and display the GitLab links in the conversation response.

**重要：不要修改项目的 `run.command` 脚本**，而是在 AI 的对话回复中直接显示链接。

Use this command to extract the links after `run.command` finishes:

```bash
python3 /Users/rokid/.codex/skills/localization-excel-updater/scripts/build_gitlab_commit_link.py \
  --workspace <workspace_path>
```

Then copy the script output into the AI's reply using this exact line format:

```text
仓库: http://gitlab.rokid-inc.com/xxx/xxx
本次提交: http://gitlab.rokid-inc.com/xxx/xxx/-/commit/abc1234
```

**关键格式要求：**
- 必须保留 `本次提交: ` 这个前缀
- 冒号后面直接跟完整 URL，不要加反引号
- 每个链接独占一行，方便客户端渲染成可点击链接
- 如果只需要回一个链接，优先至少显示 `本次提交: https://...`

This is mandatory for all Git-push workflows.

## Execution Notes

- `feishu_sync_config.json` stores the current Feishu app credentials, folder tokens, and success webhook for this local setup.
- `sync_feishu_sheet_rows.py` supports environment overrides for app credentials and folder tokens.
- `send_feishu_update_webhook.py` supports `FEISHU_NOTIFICATION_WEBHOOK` as an override.
- `send_feishu_update_webhook.py` can also derive the current commit URL from `--git-workspace` and derive the Feishu document URL from `--side` plus `--file`.
- `publish_skill_repo.py` copies the installed skill directory into a prepared Git repo without touching the repo's `.git` metadata.
- `manage_feishu_workbooks.py` supports `--dry-run` for both `download` and `pull`.
- `manage_feishu_workbooks.py` also supports `create` and `--dry-run` for create planning.
- `build_gitlab_commit_link.py` converts the current repo's `origin` remote plus `HEAD` commit into clickable GitLab URLs.
- `app端/run.command` generates Android, iOS, colors, and fonts, then commits and pushes.
- `眼镜端/applocalizationtool4anndroid/run.command` currently generates Android resources, then commits and pushes.
- If `pandas` or `openpyxl` is missing, install dependencies from the target side's `requirements.txt` before reading or writing Excel.
- If Feishu row sync fails in `add_rows` or `edit_rows`, report that the local Excel update succeeded but the cloud spreadsheet sync did not, and stop before `run.command`.
- If bulk pull succeeds locally but `run.command` fails for a selected side, report that side separately and stop before starting the next side.
- If `run.command` fails because there are no changes to commit or because push fails, explain the failure clearly and stop.
- If webhook sending fails after a successful `add_rows` or `create_workbook` push, report the webhook failure separately. Do not claim the notification was sent.
- Do not claim success until the required push step finishes successfully.

## Example Requests

- `字段：登录成功\n登录失败`
- `端：app端\n文件：home\n修改：\nkey：not_connected\n改为：未连接设备`
- `端：app端\n文件：home\n修改：\n原文：未连接\n改为：未连接设备`
- `我要新增字段\n字段：语音播报\n屏幕通知弹窗`
- `端：app端  文件：settings  字段：登录成功、登录失败`
- `app端 settings：登录成功；登录失败；网络异常，请稍后重试`
- `端：眼镜端\n文件：basic\n字段：\n蓝牙已连接\n蓝牙连接失败`
- `下载飞书 app端`
- `下载飞书 全部`
- `下载飞书\n范围：眼镜端\n文件：\nlauncher\nmedia`
- `从飞书回拉 app端 并推送 git`
- `从飞书回拉 眼镜端 launcher 和 media，覆盖本地后上传 git`
- `从飞书回拉 全部，覆盖本地并上传 git`
- `眼镜端新增一个 Widgets 表格`
- `创建表格\n端：app端\n文件：sdk_new`
- `把这个 skill 更新到我给的 Git 仓库`
- `把 Localization Excel Updater 导出并推到这个 GitHub 仓库`
