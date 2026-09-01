from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


TABLE_DESCRIPTIONS = {
    "content": "Archived file contents and cryptographic identifiers.",
    "skipped_content": "Content records not archived, with reasons and hashes.",
    "directory": "Directories stored in the archive.",
    "directory_entry": "Edges from directories to files and subdirectories.",
    "revision": "Source-code revisions (commits) and their metadata.",
    "revision_history": "Ordered parent relationships between revisions.",
    "release": "Tagged software releases and their targets.",
    "snapshot": "Repository states captured at crawl time.",
    "snapshot_branch": "Branches and targets contained in snapshots.",
    "origin": "Software origin URLs from which projects were archived.",
    "origin_visit": "Visits/crawls of software origins.",
    "origin_visit_status": "Visit results, statuses, and archived snapshot IDs.",
}

CORE_TABLES = tuple(TABLE_DESCRIPTIONS)


@dataclass(frozen=True)
class TableInfo:
    name: str
    files: int
    rows: int | None
    path: Path
    description: str


def discover_tables(dataset_path: str | Path) -> list[TableInfo]:
    root = Path(dataset_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return []

    tables: list[TableInfo] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        # Some downloaded bundles contain a nested directory with the same
        # name as the dataset root. It is a container, not an archive table.
        if child.name == root.name:
            continue
        explicit_orc = list(child.rglob("*.orc"))
        part_files = [p for p in child.rglob("part-*") if p.is_file()]
        data_files = explicit_orc or part_files
        if not data_files:
            data_files = [
                p for p in child.rglob("*")
                if p.is_file() and not p.name.startswith((".", "_"))
            ]
        if not data_files:
            continue
        tables.append(
            TableInfo(
                name=child.name,
                files=len(data_files),
                rows=None,
                path=child,
                description=TABLE_DESCRIPTIONS.get(child.name, "Dataset table."),
            )
        )
    return tables


def load_summary_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(columns=["table", "files_read", "skipped_files", "total_rows"])
    df = pd.read_csv(csv_path)
    required = {"table", "files_read", "skipped_files", "total_rows"}
    if not required.issubset(df.columns):
        return pd.DataFrame(columns=sorted(required))
    return df.copy()


def enrich_with_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "table" not in out.columns:
        return out
    out["description"] = out["table"].map(TABLE_DESCRIPTIONS).fillna("Dataset table.")
    return out


def table_names(items: Iterable[TableInfo]) -> list[str]:
    return sorted(item.name for item in items)
