#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


SIDE_DIRS = {
    "app": Path("app端"),
    "app端": Path("app端"),
    "glasses": Path("眼镜端/applocalizationtool4anndroid"),
    "眼镜端": Path("眼镜端/applocalizationtool4anndroid"),
}


def parse_args():
    parser = argparse.ArgumentParser(description="List workbook modules for a localization side.")
    parser.add_argument("--workspace", required=True, help="Workspace root containing app端 and 眼镜端/applocalizationtool4anndroid")
    parser.add_argument("--side", required=True, help="Target side: app, app端, glasses, or 眼镜端")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a numbered text list")
    return parser.parse_args()


def normalize_side(side: str) -> str:
    side = side.strip()
    if side not in SIDE_DIRS:
        supported = ", ".join(sorted(SIDE_DIRS))
        raise ValueError(f"Unsupported side: {side}. Expected one of: {supported}")
    return side


def list_modules(workspace: Path, side: str):
    excel_dir = workspace / SIDE_DIRS[side] / "excel_files"
    if not excel_dir.exists():
        raise FileNotFoundError(f"Excel directory not found: {excel_dir}")

    modules = []
    for path in sorted(excel_dir.glob("*.xlsx"), key=lambda item: item.stem.lower()):
        name = path.stem
        if name.startswith(".~") or name.startswith("~$"):
            continue
        modules.append(name)
    return excel_dir, modules


def main():
    try:
        args = parse_args()
        workspace = Path(args.workspace).expanduser().resolve()
        side = normalize_side(args.side)
        excel_dir, modules = list_modules(workspace, side)

        if args.json:
            print(json.dumps({
                "side": side,
                "excel_dir": str(excel_dir),
                "count": len(modules),
                "modules": modules,
            }, ensure_ascii=False, indent=2))
            return

        print("请选择文件：")
        for index, module in enumerate(modules, start=1):
            print(f"{index}. {module}")
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
