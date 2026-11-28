"""
CLI runner for GeoAtlas Data Freshness & Quality Monitor.

Usage:
  python scripts/check_geodata_quality.py
  python scripts/check_geodata_quality.py --check-remote --json-out quality_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from geodata_monitor import build_quality_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GeoAtlas geodata and statistical passports.")
    parser.add_argument("--check-remote", action="store_true", help="Check remote source metadata (no large downloads).")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional path to write JSON report.")
    args = parser.parse_args()

    report = build_quality_report(base_dir=BASE_DIR, check_remote=args.check_remote)
    summary = report["summary"]

    print(
        f"GeoAtlas Data Quality Report ({report['generated_at']}): "
        f"total={summary['total_datasets']}, pass={summary['passed']}, "
        f"warn={summary['warned']}, fail={summary['failed']}, "
        f"stale={summary['stale']}, unknown={summary['unknown']}"
    )
    print("-" * 88)
    for ds in report["datasets"]:
        yr = ds["latest_stat_year"] or "—"
        print(
            f"[{ds['check_result'].upper():4s} | {ds['freshness_status'].upper():7s}] "
            f"{ds['id']:26s} | {ds['region']:22s} | "
            f"cov={ds['coverage_pct']:5.1f}% | miss={ds['missing_total']:2d} | yr={yr}"
        )
        for err in ds["errors"]:
            print(f"    ERROR: {err}")
        for warn in ds["warnings"]:
            print(f"    WARN : {warn}")

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON report written to {args.json_out}")

    return 1 if summary["failed"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
