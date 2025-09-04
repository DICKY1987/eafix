#!/usr/bin/env python3
"""Placeholder trading_framework_scan tool.

This stub returns an empty framework report regardless of the bundle provided
so dependent workflows can execute during development.
"""
import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Placeholder trading_framework_scan tool")
    parser.add_argument("trading_system_bundle", help="Path to the trading system bundle (unused)")
    parser.add_argument("-o", "--output", help="Optional output JSON file; defaults to stdout")
    args = parser.parse_args()

    result = {"frameworks": []}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
