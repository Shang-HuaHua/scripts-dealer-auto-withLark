#!/usr/bin/env python3
import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


SIDE_LABELS = {
    "app": "app端",
    "app端": "app端",
    "glasses": "眼镜端",
    "眼镜端": "眼镜端",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send a Feishu bot webhook message for a successful localization update."
    )
    parser.add_argument("--side", required=True, help="Target side: app, app端, glasses, or 眼镜端")
    parser.add_argument("--file", required=True, help="Workbook module name")
    parser.add_argument("--input", required=True, help="Path to a JSON file containing row objects")
    parser.add_argument("--git-workspace", help="Optional Git workspace path used to build the latest commit URL")
    parser.add_argument("--config", help="Optional path to feishu sync config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print the payload without sending")
    return parser.parse_args()


def default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "feishu_sync_config.json"


def load_config(config_path: Optional[str]):
    path = Path(config_path).expanduser().resolve() if config_path else default_config_path()
    config = {}
    if path.exists():
        config = json.loads(path.read_text(encoding="utf-8"))
    webhook = os.getenv("FEISHU_NOTIFICATION_WEBHOOK") or config.get("notification_webhook")
    app_id = os.getenv("FEISHU_APP_ID") or config.get("app_id")
    app_secret = os.getenv("FEISHU_APP_SECRET") or config.get("app_secret")
    folders = dict(config.get("folders", {}))
    if os.getenv("FEISHU_FOLDER_APP"):
        folders["app"] = os.getenv("FEISHU_FOLDER_APP")
    if os.getenv("FEISHU_FOLDER_GLASSES"):
        folders["glasses"] = os.getenv("FEISHU_FOLDER_GLASSES")
    if not webhook:
        raise ValueError("Missing Feishu notification webhook. Set it in config or FEISHU_NOTIFICATION_WEBHOOK.")
    return {
        "webhook": webhook,
        "config_path": str(path),
        "app_id": app_id,
        "app_secret": app_secret,
        "folders": folders,
    }


def load_rows(input_path: Path):
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Input JSON must be a non-empty list")
    normalized = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be an object")
        key = str(row.get("key", "")).strip()
        zh = str(row.get("zh", "")).strip()
        if not key or not zh:
            raise ValueError(f"Row {index} must include non-empty key and zh")
        normalized.append({"key": key, "zh": zh})
    return normalized


def normalize_side_label(side: str) -> str:
    label = SIDE_LABELS.get(side.strip())
    if not label:
        supported = ", ".join(sorted(SIDE_LABELS))
        raise ValueError(f"Unsupported side: {side}. Expected one of: {supported}")
    return label


def normalize_side_key(side: str) -> str:
    normalized = side.strip()
    if normalized in ("app", "app端"):
        return "app"
    if normalized in ("glasses", "眼镜端"):
        return "glasses"
    supported = ", ".join(sorted(SIDE_LABELS))
    raise ValueError(f"Unsupported side: {side}. Expected one of: {supported}")


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
    if not config.get("app_id") or not config.get("app_secret"):
        raise ValueError("Missing Feishu app_id/app_secret. Set them in config or env vars.")
    data = api_request(
        "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json_body={"app_id": config["app_id"], "app_secret": config["app_secret"]},
    )
    if data.get("code") != 0:
        raise ValueError(f"Failed to get Feishu tenant access token: {data}")
    return data["tenant_access_token"]


def list_folder_files(token: str, folder_token: str):
    files = []
    page_token = ""
    while True:
        url = f"https://open.feishu.cn/open-apis/drive/v1/files?folder_token={folder_token}&page_size=200"
        if page_token:
            url += f"&page_token={urllib.parse.quote(page_token, safe='')}"
        data = api_request("GET", url, token=token)
        if data.get("code") != 0:
            raise ValueError(f"Failed to list Feishu folder: {data}")
        block = data.get("data", {})
        files.extend(block.get("files", []))
        if not block.get("has_more"):
            break
        page_token = block.get("next_page_token") or ""
        if not page_token:
            break
    return files


def resolve_spreadsheet_url(config, side: str, module: str) -> str:
    folder_token = config.get("folders", {}).get(side)
    if not folder_token:
        raise ValueError(f"Missing Feishu folder token for side: {side}")
    token = get_tenant_access_token(config)
    files = list_folder_files(token, folder_token)
    exact = None
    lowered = module.lower()
    for item in files:
        if item.get("type") != "sheet":
            continue
        name = str(item.get("name", "")).strip()
        if name == module:
            exact = item
            break
        if exact is None and name.lower() == lowered:
            exact = item
    if exact is None:
        raise FileNotFoundError(f"Feishu spreadsheet not found for module '{module}'")
    return exact.get("url") or f"https://my.feishu.cn/sheets/{exact['token']}"


def run_git(args, workspace: Path) -> str:
    import subprocess

    result = subprocess.run(
        ["git", *args],
        cwd=str(workspace),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def normalize_remote_url(remote_url: str) -> str:
    value = remote_url.strip()
    if value.endswith(".git"):
        value = value[:-4]
    if value.startswith("git@"):
        host_and_path = value[4:]
        host, path = host_and_path.split(":", 1)
        return f"http://{host}/{path}"
    if value.startswith("ssh://git@"):
        host_and_path = value[len("ssh://git@") :]
        host, path = host_and_path.split("/", 1)
        if ":" in host:
            host = host.split(":", 1)[0]
        return f"http://{host}/{path}"
    if value.startswith("http://") or value.startswith("https://"):
        return value
    raise ValueError(f"Unsupported Git remote format: {remote_url}")


def build_git_links(workspace_path: str):
    workspace = Path(workspace_path).expanduser().resolve()
    remote_url = run_git(["remote", "get-url", "origin"], workspace)
    repository_url = normalize_remote_url(remote_url)
    commit_sha = run_git(["rev-parse", "HEAD"], workspace)
    return {
        "repository_url": repository_url,
        "commit_url": f"{repository_url}/-/commit/{commit_sha}",
    }


def build_payload(side_label: str, module: str, rows, commit_url: Optional[str], spreadsheet_url: Optional[str]):
    lines = [f"- {row['key']} | {row['zh']}" for row in rows]
    text_lines = [
        "Localization Excel Updater 更新成功",
        f"端：{side_label}",
        f"文件：{module}",
        "最近添加：",
        *lines,
    ]
    if commit_url:
        text_lines.append(f"最近提交：{commit_url}")
    if spreadsheet_url:
        text_lines.append(f"飞书文档：{spreadsheet_url}")
    text = "\n".join(text_lines)
    return {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }


def send_webhook(webhook: str, payload):
    request = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    try:
        args = parse_args()
        side_label = normalize_side_label(args.side)
        side_key = normalize_side_key(args.side)
        module = args.file[:-5] if args.file.endswith(".xlsx") else args.file
        rows = load_rows(Path(args.input).expanduser().resolve())
        config = load_config(args.config)
        commit_url = None
        if args.git_workspace:
            commit_url = build_git_links(args.git_workspace)["commit_url"]
        spreadsheet_url = resolve_spreadsheet_url(config, side_key, module)
        payload = build_payload(side_label, module, rows, commit_url, spreadsheet_url)

        if args.dry_run:
            print(json.dumps({"webhook": config["webhook"], "payload": payload}, ensure_ascii=False, indent=2))
            return

        result = send_webhook(config["webhook"], payload)
        print(json.dumps({"webhook": config["webhook"], "result": result}, ensure_ascii=False, indent=2))
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
