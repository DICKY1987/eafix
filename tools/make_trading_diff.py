#!/usr/bin/env python3
"""Placeholder make_trading_diff tool.

Generates an empty unified diff regardless of the artifacts supplied so test
pipelines can exercise a diff step.
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Placeholder make_trading_diff tool")
    parser.add_argument("artifact_vN", help="Original artifact (unused)")
    parser.add_argument("artifact_vN1", help="Updated artifact (unused)")
    parser.add_argument("-o", "--output", help="Optional output diff file; defaults to stdout")
    args = parser.parse_args()

    diff_text = ""  # No differences in placeholder implementation

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(diff_text)
    else:
        print(diff_text)


if __name__ == "__main__":
    main()
