#!/usr/bin/env python3
import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


SIDE_ALIASES = {
    "app": "app",
    "app端": "app",
    "glasses": "glasses",
    "眼镜端": "glasses",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync localization rows into the matching Feishu spreadsheet."
    )
    parser.add_argument("--side", required=True, help="Target side: app, app端, glasses, or 眼镜端")
    parser.add_argument("--file", required=True, help="Workbook module name with or without .xlsx")
    parser.add_argument("--input", required=True, help="Path to a JSON file containing row objects")
    parser.add_argument(
        "--config",
        help="Optional path to feishu sync config JSON. Defaults to feishu_sync_config.json beside the skill.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Resolve and plan updates without writing to Feishu")
    return parser.parse_args()


def normalize_side(side: str) -> str:
    normalized = SIDE_ALIASES.get(side.strip())
    if normalized is None:
        supported = ", ".join(sorted(SIDE_ALIASES))
        raise ValueError(f"Unsupported side: {side}. Expected one of: {supported}")
    return normalized


def normalize_module_name(file_name: str) -> str:
    return file_name[:-5] if file_name.endswith(".xlsx") else file_name


def default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "feishu_sync_config.json"


def load_config(config_path: Optional[str]):
    path = Path(config_path).expanduser().resolve() if config_path else default_config_path()
    config = {}
    if path.exists():
        config = json.loads(path.read_text(encoding="utf-8"))

    app_id = os.getenv("FEISHU_APP_ID") or config.get("app_id")
    app_secret = os.getenv("FEISHU_APP_SECRET") or config.get("app_secret")
    folders = dict(config.get("folders", {}))
    if os.getenv("FEISHU_FOLDER_APP"):
        folders["app"] = os.getenv("FEISHU_FOLDER_APP")
    if os.getenv("FEISHU_FOLDER_GLASSES"):
        folders["glasses"] = os.getenv("FEISHU_FOLDER_GLASSES")

    if not app_id or not app_secret:
        raise ValueError("Missing Feishu app_id/app_secret. Set them in config or env vars.")
    if not folders.get("app") or not folders.get("glasses"):
        raise ValueError("Missing Feishu folder tokens for app/glasses.")

    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "folders": folders,
        "config_path": str(path),
    }


def load_rows(input_path: Path):
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Input JSON must be a non-empty list")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be an object")
        row = resolve_external_value_refs(row, input_path.parent)
        key = row.get("key")
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"Row {index} is missing a non-empty key")
        row["key"] = key.strip()
        rows[index - 1] = row
    return rows


def resolve_external_value_refs(row, base_dir: Path):
    resolved = {}
    for key, value in row.items():
        if isinstance(value, str) and value.startswith("@file:"):
            file_path = Path(value[len("@file:"):]).expanduser()
            if not file_path.is_absolute():
                file_path = (base_dir / file_path).resolve()
            if not file_path.exists():
                raise FileNotFoundError(f"Referenced text file not found for header '{key}': {file_path}")
            resolved[key] = file_path.read_text(encoding="utf-8")
        else:
            resolved[key] = value
    return resolved


def api_request(method: str, url: str, token: Optional[str] = None, json_body=None):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_tenant_access_token(config):
    data = api_request(
        "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json_body={"app_id": config["app_id"], "app_secret": config["app_secret"]},
    )
    if data.get("code") != 0:
        raise ValueError(f"Failed to get Feishu tenant access token: {data}")
    return data["tenant_access_token"]


def list_folder_files(token: str, folder_token: str):
    data = api_request(
        "GET",
        f"https://open.feishu.cn/open-apis/drive/v1/files?folder_token={folder_token}&page_size=200",
        token=token,
    )
    if data.get("code") != 0:
        raise ValueError(f"Failed to list Feishu folder: {data}")
    return data.get("data", {}).get("files", [])


def find_spreadsheet(files, module_name: str):
    exact = [file for file in files if file.get("name") == module_name and file.get("type") == "sheet"]
    if exact:
        return exact[0]

    lowered = module_name.lower()
    case_insensitive = [
        file for file in files
        if str(file.get("name", "")).lower() == lowered and file.get("type") == "sheet"
    ]
    if case_insensitive:
        return case_insensitive[0]

    available = sorted(file.get("name", "") for file in files if file.get("type") == "sheet")
    raise FileNotFoundError(f"Feishu spreadsheet not found for module '{module_name}'. Available: {available}")


def get_spreadsheet_metainfo(token: str, spreadsheet_token: str):
    data = api_request(
        "GET",
        f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo",
        token=token,
    )
    if data.get("code") != 0:
        raise ValueError(f"Failed to get spreadsheet metainfo: {data}")
    return data["data"]


def read_sheet_range(token: str, spreadsheet_token: str, range_expr: str):
    encoded = urllib.parse.quote(range_expr, safe="")
    data = api_request(
        "GET",
        f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{encoded}",
        token=token,
    )
    if data.get("code") != 0:
        raise ValueError(f"Failed to read sheet range {range_expr}: {data}")
    return data["data"]["valueRange"].get("values", [])


def update_sheet_range(token: str, spreadsheet_token: str, range_expr: str, values):
    data = api_request(
        "PUT",
        f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values",
        token=token,
        json_body={"valueRange": {"range": range_expr, "values": values}},
    )
    if data.get("code") != 0:
        raise ValueError(f"Failed to update sheet range {range_expr}: {data}")
    return data["data"]


def sanitize_headers(header_row):
    headers = []
    for cell in header_row:
        if cell is None or str(cell).strip() == "":
            break
        headers.append(str(cell).strip())
    if not headers or headers[0] != "key":
        raise ValueError("Feishu sheet header row must start with key")
    return headers


def column_letter(index: int) -> str:
    letters = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def read_headers_and_key_rows(token: str, spreadsheet_token: str, sheet_id: str, column_count: int, row_count: int):
    last_col = column_letter(column_count)
    header_values = read_sheet_range(token, spreadsheet_token, f"{sheet_id}!A1:{last_col}1")
    headers = sanitize_headers(header_values[0] if header_values else [])

    key_values = read_sheet_range(token, spreadsheet_token, f"{sheet_id}!A2:A{row_count}")
    key_to_row = {}
    last_nonempty_key_row = 1
    for offset, row in enumerate(key_values, start=2):
        value = row[0] if row else None
        if value is None or str(value).strip() == "":
            continue
        key = str(value).strip()
        key_to_row[key] = offset
        last_nonempty_key_row = offset
    return headers, key_to_row, last_nonempty_key_row


def build_row_values(headers, row, existing_values=None):
    values = []
    existing_values = existing_values or []
    for index, header in enumerate(headers):
        if header in row:
            values.append(row.get(header, ""))
        elif index < len(existing_values):
            values.append(existing_values[index])
        else:
            values.append("")
    return values


def sync_rows(token: str, spreadsheet_token: str, sheet_id: str, headers, key_to_row, last_nonempty_key_row, rows, dry_run: bool):
    last_col = column_letter(len(headers))
    next_row = last_nonempty_key_row + 1
    updated = []
    appended = []

    for row in rows:
        key = row["key"]
        target_row = key_to_row.get(key)
        operation = "update"
        if target_row is None:
            target_row = next_row
            next_row += 1
            operation = "append"

        range_expr = f"{sheet_id}!A{target_row}:{last_col}{target_row}"
        existing_values = None
        if operation == "update":
            current_values = read_sheet_range(token, spreadsheet_token, range_expr)
            existing_values = current_values[0] if current_values else []
        values = [build_row_values(headers, row, existing_values)]
        if not dry_run:
            update_sheet_range(token, spreadsheet_token, range_expr, values)

        result = {"key": key, "row": target_row, "range": range_expr}
        if operation == "update":
            updated.append(result)
        else:
            appended.append(result)

    return updated, appended


def main():
    try:
        args = parse_args()
        side = normalize_side(args.side)
        module_name = normalize_module_name(args.file)
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Input JSON not found: {input_path}")

        rows = load_rows(input_path)
        config = load_config(args.config)
        token = get_tenant_access_token(config)
        files = list_folder_files(token, config["folders"][side])
        spreadsheet = find_spreadsheet(files, module_name)
        metainfo = get_spreadsheet_metainfo(token, spreadsheet["token"])
        first_sheet = metainfo["sheets"][0]
        headers, key_to_row, last_nonempty_key_row = read_headers_and_key_rows(
            token,
            spreadsheet["token"],
            first_sheet["sheetId"],
            first_sheet["columnCount"],
            first_sheet["rowCount"],
        )
        updated, appended = sync_rows(
            token,
            spreadsheet["token"],
            first_sheet["sheetId"],
            headers,
            key_to_row,
            last_nonempty_key_row,
            rows,
            args.dry_run,
        )

        print(json.dumps(
            {
                "side": side,
                "module": module_name,
                "spreadsheet_token": spreadsheet["token"],
                "spreadsheet_url": spreadsheet.get("url"),
                "sheet_id": first_sheet["sheetId"],
                "sheet_title": first_sheet["title"],
                "headers": headers,
                "updated_rows": updated,
                "appended_rows": appended,
                "dry_run": args.dry_run,
            },
            ensure_ascii=False,
            indent=2,
        ))
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
