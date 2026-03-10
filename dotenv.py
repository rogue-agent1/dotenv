#!/usr/bin/env python3
"""dotenv - Parse, validate, and diff .env files.

One file. Zero deps. Manages env files.

Usage:
  dotenv.py parse .env                    → list key=value pairs
  dotenv.py get .env DATABASE_URL         → get single value
  dotenv.py diff .env .env.example        → find missing/extra vars
  dotenv.py validate .env .env.example    → check all required vars present
  dotenv.py merge .env .env.local         → merge (local overrides)
  dotenv.py export .env                   → output as export statements
"""

import argparse
import re
import sys
from collections import OrderedDict


def parse_env(path: str) -> OrderedDict:
    """Parse a .env file into an ordered dict."""
    env = OrderedDict()
    try:
        with open(path) as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Handle: KEY=VALUE, KEY="VALUE", KEY='VALUE', export KEY=VALUE
                line = re.sub(r'^export\s+', '', line)
                m = re.match(r'''([A-Za-z_][A-Za-z0-9_]*)=(.*)$''', line)
                if not m:
                    continue
                key = m.group(1)
                val = m.group(2).strip()
                # Unquote
                if (val.startswith('"') and val.endswith('"')) or \
                   (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                # Handle inline comments (only for unquoted values)
                elif '#' in val:
                    val = val.split('#')[0].strip()
                env[key] = val
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return env


def cmd_parse(args):
    env = parse_env(args.file)
    if args.json:
        import json
        print(json.dumps(dict(env), indent=2))
    else:
        for k, v in env.items():
            print(f"{k}={v}")
    return 0


def cmd_get(args):
    env = parse_env(args.file)
    if args.key in env:
        print(env[args.key])
        return 0
    print(f"Key not found: {args.key}", file=sys.stderr)
    return 1


def cmd_diff(args):
    a = parse_env(args.file1)
    b = parse_env(args.file2)
    ka, kb = set(a.keys()), set(b.keys())

    only_a = ka - kb
    only_b = kb - ka
    changed = {k for k in ka & kb if a[k] != b[k]}

    if only_a:
        print(f"Only in {args.file1}:")
        for k in sorted(only_a):
            print(f"  - {k}={a[k]}")
    if only_b:
        print(f"Only in {args.file2}:")
        for k in sorted(only_b):
            print(f"  + {k}={b[k]}")
    if changed:
        print("Changed:")
        for k in sorted(changed):
            print(f"  ~ {k}: {a[k]!r} → {b[k]!r}")
    if not only_a and not only_b and not changed:
        print("Files are identical")
        return 0
    return 1 if (only_a or only_b) else 0


def cmd_validate(args):
    env = parse_env(args.file)
    template = parse_env(args.template)
    missing = set(template.keys()) - set(env.keys())
    empty = [k for k in template if k in env and not env[k]]

    ok = True
    if missing:
        print("Missing variables:")
        for k in sorted(missing):
            print(f"  ✗ {k}")
        ok = False
    if empty and args.no_empty:
        print("Empty variables:")
        for k in sorted(empty):
            print(f"  ⚠ {k}")
        ok = False
    if ok:
        print(f"✓ All {len(template)} required variables present")
    return 0 if ok else 1


def cmd_merge(args):
    base = parse_env(args.base)
    override = parse_env(args.override)
    merged = OrderedDict(base)
    merged.update(override)
    for k, v in merged.items():
        print(f"{k}={v}")
    return 0


def cmd_export(args):
    env = parse_env(args.file)
    for k, v in env.items():
        # Shell-safe quoting
        if ' ' in v or '"' in v or "'" in v or '$' in v:
            v = v.replace("'", "'\\''")
            print(f"export {k}='{v}'")
        else:
            print(f"export {k}={v}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Parse, validate, and diff .env files")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("parse", help="Parse and list env vars")
    p.add_argument("file")
    p.add_argument("--json", action="store_true")

    g = sub.add_parser("get", help="Get single variable")
    g.add_argument("file")
    g.add_argument("key")

    d = sub.add_parser("diff", help="Diff two env files")
    d.add_argument("file1")
    d.add_argument("file2")

    v = sub.add_parser("validate", help="Validate against template")
    v.add_argument("file")
    v.add_argument("template", help=".env.example or template file")
    v.add_argument("--no-empty", action="store_true", help="Fail on empty values")

    m = sub.add_parser("merge", help="Merge env files (second overrides)")
    m.add_argument("base")
    m.add_argument("override")

    e = sub.add_parser("export", help="Output as shell export statements")
    e.add_argument("file")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    cmds = {"parse": cmd_parse, "get": cmd_get, "diff": cmd_diff,
            "validate": cmd_validate, "merge": cmd_merge, "export": cmd_export}
    return cmds[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
