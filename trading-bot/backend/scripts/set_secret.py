from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path


ALLOWED_KEYS = {
    "OPENAI_API_KEY",
    "OPENAI_ANALYST_MODEL",
    "JQUANTS_API_KEY",
    "JQUANTS_EMAIL",
    "JQUANTS_PASSWORD",
    "DATA_SOURCE",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely update local .env secrets without echoing values.")
    parser.add_argument("key", choices=sorted(ALLOWED_KEYS))
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--value", help="Non-secret value. Avoid this for API keys or passwords.")
    parser.add_argument("--stdin", action="store_true", help="Read the value from stdin without echoing it.")
    args = parser.parse_args()

    if args.stdin:
        value = sys.stdin.read().strip()
    else:
        value = args.value if args.value is not None else getpass.getpass(f"{args.key}: ")
    if not value:
        raise SystemExit("Value is empty. Nothing was changed.")

    env_path = Path(args.env_file)
    rows = _read_env_rows(env_path)
    updated = False
    for index, row in enumerate(rows):
        if row.startswith(f"{args.key}="):
            rows[index] = f"{args.key}={value}"
            updated = True
            break
    if not updated:
        rows.append(f"{args.key}={value}")

    env_path.write_text("\n".join(rows).rstrip() + "\n", encoding="utf-8")
    print(f"Updated {args.key} in {env_path}")


def _read_env_rows(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


if __name__ == "__main__":
    main()
