#!/usr/bin/env python3
"""dotenv - Parse, validate, diff, and merge .env files.

Usage:
    dotenv list .env                      # list key=value pairs
    dotenv get .env DATABASE_URL          # get single value
    dotenv diff .env .env.production      # diff two env files
    dotenv merge .env .env.local          # merge (local overrides)
    dotenv check .env .env.example        # find missing keys
    dotenv template .env                  # generate .env.example (strip values)
    dotenv validate .env --required KEY1 KEY2  # ensure keys exist
"""
import argparse
import os
import re
import sys


def parse_env(filepath: str) -> list[dict]:
    """Parse .env file into ordered list of entries."""
    entries = []
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found", file=sys.stderr)
        sys.exit(1)

    with open(filepath) as f:
        for lineno, line in enumerate(f, 1):
            raw = line.rstrip('\n')
            stripped = raw.strip()

            if not stripped or stripped.startswith('#'):
                entries.append({"type": "comment" if stripped.startswith('#') else "blank",
                                "raw": raw, "line": lineno})
                continue

            # Handle export prefix
            if stripped.startswith("export "):
                stripped = stripped[7:].strip()

            m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', stripped)
            if not m:
                entries.append({"type": "invalid", "raw": raw, "line": lineno})
                continue

            key = m.group(1)
            val = m.group(2).strip()

            # Unquote
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]

            entries.append({"type": "var", "key": key, "value": val, "raw": raw, "line": lineno})

    return entries


def env_dict(filepath: str) -> dict[str, str]:
    """Parse .env into simple dict."""
    return {e["key"]: e["value"] for e in parse_env(filepath) if e["type"] == "var"}


def cmd_list(args):
    entries = parse_env(args.file)
    for e in entries:
        if e["type"] == "var":
            val = e["value"]
            if args.mask and any(k in e["key"].upper() for k in ("SECRET", "PASSWORD", "TOKEN", "KEY", "API")):
                val = val[:3] + "***" if len(val) > 3 else "***"
            print(f"  {e['key']}={val}")
        elif e["type"] == "invalid":
            print(f"  ⚠️  Line {e['line']}: {e['raw']}")
    total = sum(1 for e in entries if e["type"] == "var")
    print(f"\n  {total} variables in {args.file}")


def cmd_get(args):
    d = env_dict(args.file)
    if args.key in d:
        print(d[args.key])
    else:
        print(f"Error: {args.key} not found in {args.file}", file=sys.stderr)
        sys.exit(1)


def cmd_diff(args):
    a = env_dict(args.file1)
    b = env_dict(args.file2)
    all_keys = sorted(set(list(a.keys()) + list(b.keys())))

    added = removed = changed = same = 0
    for key in all_keys:
        va = a.get(key)
        vb = b.get(key)
        if va is None:
            print(f"  + {key}={vb}")
            added += 1
        elif vb is None:
            print(f"  - {key}={va}")
            removed += 1
        elif va != vb:
            print(f"  ~ {key}")
            print(f"    < {va}")
            print(f"    > {vb}")
            changed += 1
        else:
            same += 1

    print(f"\n  {same} same, {added} added, {removed} removed, {changed} changed")


def cmd_merge(args):
    base = env_dict(args.base)
    override = env_dict(args.override)
    merged = {**base, **override}
    for key in sorted(merged):
        src = "override" if key in override and (key not in base or base[key] != override[key]) else "base"
        mark = " # ← override" if src == "override" and key in base else ""
        print(f"{key}={merged[key]}{mark}")


def cmd_check(args):
    actual = env_dict(args.file)
    example = env_dict(args.example)

    missing = [k for k in example if k not in actual]
    extra = [k for k in actual if k not in example]

    if missing:
        print(f"  ❌ Missing ({len(missing)}):")
        for k in missing:
            print(f"     {k}")
    if extra:
        print(f"  ℹ️  Extra ({len(extra)}):")
        for k in extra:
            print(f"     {k}")
    if not missing:
        print(f"  ✅ All {len(example)} required keys present")
    else:
        sys.exit(1)


def cmd_template(args):
    entries = parse_env(args.file)
    for e in entries:
        if e["type"] == "comment" or e["type"] == "blank":
            print(e["raw"])
        elif e["type"] == "var":
            print(f"{e['key']}=")


def cmd_validate(args):
    d = env_dict(args.file)
    missing = [k for k in args.required if k not in d]
    empty = [k for k in args.required if k in d and not d[k]]

    if missing:
        print(f"  ❌ Missing: {', '.join(missing)}")
    if empty:
        print(f"  ⚠️  Empty: {', '.join(empty)}")
    if not missing and not empty:
        print(f"  ✅ All {len(args.required)} required keys present and non-empty")
    if missing:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=".env file toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="List variables")
    p.add_argument("file")
    p.add_argument("--mask", action="store_true", help="Mask sensitive values")

    p = sub.add_parser("get", help="Get single value")
    p.add_argument("file")
    p.add_argument("key")

    p = sub.add_parser("diff", help="Diff two env files")
    p.add_argument("file1")
    p.add_argument("file2")

    p = sub.add_parser("merge", help="Merge env files")
    p.add_argument("base")
    p.add_argument("override")

    p = sub.add_parser("check", help="Check against example")
    p.add_argument("file")
    p.add_argument("example")

    p = sub.add_parser("template", help="Generate template (strip values)")
    p.add_argument("file")

    p = sub.add_parser("validate", help="Validate required keys")
    p.add_argument("file")
    p.add_argument("--required", nargs="+", required=True)

    args = parser.parse_args()
    cmds = {"list": cmd_list, "get": cmd_get, "diff": cmd_diff, "merge": cmd_merge,
            "check": cmd_check, "template": cmd_template, "validate": cmd_validate}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
