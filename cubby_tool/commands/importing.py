import json
import subprocess
import sys
from pathlib import Path

from cubby_tool import keyring, store, style
from cubby_tool.commands._common import _resolve


def _parse_env_file(path: Path) -> dict:
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key.strip()] = value
    return result


def _fetch_aws_secret(secret_id: str, region: str | None) -> dict:
    cmd = ["aws", "secretsmanager", "get-secret-value",
           "--secret-id", secret_id, "--query", "SecretString", "--output", "text"]
    if region:
        cmd += ["--region", region]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _parse_json_file(path: Path) -> dict:
    """Parse a flat JSON object {name: value} into a dict of string values."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"import: {path} must contain a flat JSON object")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            raise ValueError(f"import: {path} value for '{key}' must be a scalar, "
                             f"not a {type(value).__name__}")
    return {k: str(v) for k, v in data.items()}


def _fetch_1password(vault: str) -> dict:
    """Fetch every item from a 1Password vault via the `op` CLI. One secret per
    item: name = item title, value = the item's password (else first concealed)
    field. Items with no such field are skipped."""
    listing = subprocess.run(
        ["op", "item", "list", "--vault", vault, "--format", "json"],
        capture_output=True, text=True, check=True)
    pairs = {}
    for item in json.loads(listing.stdout):
        detail = subprocess.run(
            ["op", "item", "get", item["id"], "--format", "json"],
            capture_output=True, text=True, check=True)
        fields = json.loads(detail.stdout).get("fields", [])
        value = next((f["value"] for f in fields
                      if f.get("purpose") == "PASSWORD" and f.get("value")), None)
        if value is None:
            value = next((f["value"] for f in fields
                          if f.get("type") == "CONCEALED" and f.get("value")), None)
        if value is not None:
            pairs[item["title"]] = value
    return pairs


def cmd_import(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)

    if args.source_type in ("dotenv", "json"):
        path = Path(args.source)
        if not path.exists():
            print(style.fail(f"import: file not found: {args.source}"), file=sys.stderr)
            return 2
        pairs = _parse_env_file(path) if args.source_type == "dotenv" \
            else _parse_json_file(path)
    elif args.source_type == "aws":
        try:
            pairs = _fetch_aws_secret(args.source, args.region)
        except FileNotFoundError:
            print(style.fail("import: aws CLI not found (install awscli)"),
                  file=sys.stderr)
            return 2
    elif args.source_type == "1password":
        try:
            pairs = _fetch_1password(args.source)
        except FileNotFoundError:
            print(style.fail("import: op CLI not found (install the 1Password CLI)"),
                  file=sys.stderr)
            return 2
    elif args.source_type == "ns":
        if args.source == ns:
            print(style.fail(f"import: cannot import namespace '{ns}' onto itself"),
                  file=sys.stderr)
            return 4
        if args.source not in cfg.namespaces:
            print(style.fail(f"import: namespace '{args.source}' not found"),
                  file=sys.stderr)
            return 4
        pairs = store.read_values(home, args.source, identity)
    else:  # unreachable — argparse `choices` guards the type
        print(style.fail(f"import: unknown source type '{args.source_type}'"),
              file=sys.stderr)
        return 2

    for name, value in pairs.items():
        store.set_secret(home, ns, name, str(value), identity, recipient)
    print(style.ok(f"imported {len(pairs)} secret(s) into namespace '{ns}'"))
    return 0
