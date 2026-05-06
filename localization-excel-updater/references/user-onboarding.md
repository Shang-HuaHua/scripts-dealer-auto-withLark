# User Onboarding

Use this reference when the user asks how to share, install, or first-use this skill.

## Install For Another User

This skill is a folder-based local skill. The target user only needs this folder:

- `localization-excel-updater/`

Install by copying the folder to:

```text
~/.codex/skills/localization-excel-updater
```

Required files:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/append_excel_rows.py`
- `scripts/update_excel_rows.py`
- `scripts/sync_feishu_sheet_rows.py`
- `scripts/manage_feishu_workbooks.py`
- `scripts/list_workbooks.py`
- `scripts/send_feishu_update_webhook.py`
- `scripts/publish_skill_repo.py`
- `feishu_sync_config.json`
- `references/workspace-layout.md`
- `references/feishu-sync.md`
- `references/user-onboarding.md`

Then restart Codex so the new skill is loaded.

## Share Package

When sharing the skill with another user, recommend one of these methods:

1. Send the whole `localization-excel-updater` folder.
2. Put the folder in a Git repo and ask them to copy it into `~/.codex/skills/`.
3. Zip the folder, then ask them to unzip it into `~/.codex/skills/`.
4. Put the folder in a dedicated Git repo and keep future skill updates synced there.

## First-Use Checklist

Before the first real run, the user should:

1. Open the localization workspace root that contains both:
   - `app端/`
   - `眼镜端/applocalizationtool4anndroid/`
2. Make sure `python3` is available.
3. Make sure Excel dependencies are available.
4. Make sure `feishu_sync_config.json` contains the correct Feishu app credentials, folder tokens, and success webhook for the target tenant.

If the first run reports missing `pandas` or `openpyxl`, install them with:

```bash
cd app端
pip3 install -r requirements.txt --break-system-packages
```

If they mainly work on the glasses side, they can also run:

```bash
cd 眼镜端/applocalizationtool4anndroid
pip3 install -r requirements.txt --break-system-packages
```

## First-Use Prompts

### Add Rows

Recommend this first-use entry:

```text
用 $localization-excel-updater

字段：
登录成功
登录失败
```

Then the skill should guide them through:

1. Choose side:
   - `1. app端`
   - `2. 眼镜端`
2. Choose file:
   - from the current local workbook list under `excel_files/*.xlsx`
   - by number, or
   - by file name
3. Wait for reset, local Excel update, Feishu row sync, resource generation, commit, push, and success webhook

### Edit Existing Rows

Recommend:

```text
用 $localization-excel-updater

端：app端
文件：home
修改：
key：not_connected
改为：未连接设备
```

Or:

```text
用 $localization-excel-updater

端：app端
文件：home
修改：
原文：未连接
改为：未连接设备
```

This will:

1. Run `reset.command`
2. Locate the existing row by `key` or current Chinese text
3. Update the local workbook row while keeping the same `key`
4. Sync the updated row to Feishu
5. Run `run.command`
6. Commit and push
7. Send a Feishu group notification with the updated text and links

### Bulk Download

Recommend:

```text
用 $localization-excel-updater
下载飞书 app端
```

Or:

```text
用 $localization-excel-updater
下载飞书 全部
```

This downloads Feishu spreadsheets into a local folder and does not change Git.

### Pull From Feishu To Git

Recommend:

```text
用 $localization-excel-updater
从飞书回拉 app端 并上传 git
```

Or:

```text
用 $localization-excel-updater
从飞书回拉 全部，覆盖本地后上传 git
```

This will:

1. Run `reset.command`
2. Overwrite local `excel_files/*.xlsx` with Feishu content
3. Run `run.command`
4. Commit and push
5. Show `本次提交: https://...` for the pushed GitLab commit

### Create A New Workbook

Recommend:

```text
用 $localization-excel-updater
眼镜端新增一个 Widgets 表格
```

Or:

```text
用 $localization-excel-updater
创建表格
端：app端
文件：sdk_new
```

This will:

1. Run `reset.command`
2. Create the new local workbook under `excel_files/`
3. Create the matching Feishu spreadsheet
4. Write the standard header row to both
5. Run `run.command`
6. Commit and push

### Publish The Skill Repo

Recommend:

```text
把这个 skill 更新到我给的 Git 仓库
本地仓库：/path/to/repo
```

Or:

```text
把 Localization Excel Updater 导出并推到这个仓库：
git@github.com:xxx/yyy.git
```

This will:

1. Copy the latest installed skill folder into the target repo
2. Optionally include the Chinese update-and-usage document
3. Stage the changed files
4. Commit the repo update
5. Push it to the configured remote

## What The User Should Expect

Explain this clearly:

- The skill edits the source `.xlsx` file directly in `add_rows` mode.
- The skill can also edit an existing row in place while keeping the same `key`.
- If the user types visible escape sequences like `\n`, the skill should keep them as literal text in the workbook instead of converting them into actual line breaks.
- The skill can also publish its own latest files into a provided Git repository for backup or sharing.
- It runs `reset.command` before any local append or local overwrite workflow.
- In `add_rows`, it syncs the same rows into the matching Feishu spreadsheet before running `run.command`.
- In bulk pull mode, it uses Feishu spreadsheets to overwrite local `excel_files/*.xlsx`.
- File selection is dynamic: the picker reads the current local `excel_files/*.xlsx` directory instead of using a hardcoded workbook list.
- In create-workbook mode, it creates both the local workbook and the matching Feishu spreadsheet before pushing Git.
- It runs `run.command` after a successful local update workflow.
- It tries to commit and push automatically in Git workflows.
- After a successful Git push, it should show a clickable line in the reply such as `本次提交: https://...`.
- After a successful `add_rows` or `edit_rows` push, it sends a Feishu webhook notification containing the updated `key`, Chinese text, latest Git commit URL, and the matching Feishu document URL.
- Download mode only exports spreadsheets locally and does not touch Git.
- If Feishu sync fails, the skill should stop before `run.command` and report the cloud-sync failure.
- If Git push fails because of SSH or network issues, the skill should report that the local commit succeeded but remote push did not.

## Suggested Short Install Message

Use this wording when the user wants a short install guide:

```text
把 `localization-excel-updater` 整个文件夹复制到 `~/.codex/skills/` 下，确认 `feishu_sync_config.json` 里的飞书配置和 webhook 可用，然后重启 Codex。首次使用时，在多语言工作区根目录里可以直接输入：

用 $localization-excel-updater

字段：
登录成功
登录失败

如果要整端下载飞书表格，就输入 `下载飞书 app端` 或 `下载飞书 全部`；如果要把飞书内容覆盖回本地并上传 git，就输入 `从飞书回拉 app端 并上传 git` 或 `从飞书回拉 全部，覆盖本地后上传 git`。
```
