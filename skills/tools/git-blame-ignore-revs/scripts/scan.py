#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from common import git_root, parse_revs_file, resolve_revs_file, scan_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan full branch history for formatting-only commits.")
    parser.add_argument("--file", help="Explicit ignore-revs file path (overrides git config).")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    target = resolve_revs_file(root, args.file)
    active, _ = parse_revs_file(target)
    result = scan_history(set(active))
    result["file"] = str(target)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"scanned={result['scanned']} already_ignored_or_skipped={result['already_ignored_or_skipped']}")
        to_add = result["to_add"]
        propose = result["propose"]
        assert isinstance(to_add, list) and isinstance(propose, list)
        print(f"high-confidence to add: {len(to_add)}")
        for entry in to_add:
            assert isinstance(entry, dict)
            print(f"  {entry['short']} {entry['date']} {entry['subject']}")
        print(f"medium-confidence to propose: {len(propose)}")
        for entry in propose:
            assert isinstance(entry, dict)
            print(f"  {entry['short']} {entry['date']} {entry['subject']} [{entry['evidence']}]")
        print(f"low (ignored): {result['low_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
