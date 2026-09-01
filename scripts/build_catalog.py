from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.catalog import discover_tables
from src.query_engine import SWHQueryEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a row-count catalog for a local Software Heritage ORC export.")
    parser.add_argument("dataset_path")
    parser.add_argument("--output", default="table_summary.csv")
    args = parser.parse_args()

    root = Path(args.dataset_path).expanduser().resolve()
    engine = SWHQueryEngine(root)
    discovered = {item.name: item for item in discover_tables(root)}
    rows = []
    for table in engine.tables:
        info = discovered[table]
        try:
            count = engine.count(table)
            skipped = 0
        except Exception:
            count = 0
            skipped = info.files
        rows.append({"table": table, "files_read": max(info.files - skipped, 0), "skipped_files": skipped, "total_rows": count})
        print(f"{table}: {count:,}")
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
