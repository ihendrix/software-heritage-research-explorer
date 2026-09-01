from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.orc as orc

from .catalog import discover_tables
from .sql_utils import quote_identifier


ALLOWED_OPERATORS = {
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
    "starts_with",
    "is_null",
    "not_null",
}


class SWHQueryEngine:
    """
    Read-only query layer over a local Software Heritage ORC export.

    PyArrow handles ORC decoding.
    DuckDB handles SQL filtering and analytics over Arrow tables.
    """

    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path).expanduser().resolve()
        self.connection = duckdb.connect(database=":memory:")
        self._tables = {t.name for t in discover_tables(self.dataset_path)}

    @property
    def tables(self) -> list[str]:
        return sorted(self._tables)

    def has_table(self, table: str) -> bool:
        return table in self._tables

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def _files(self, table: str) -> list[Path]:
        if table not in self._tables:
            raise ValueError(f"Unknown or unavailable table: {table}")

        table_path = self.dataset_path / table

        explicit_orc = sorted(
            p for p in table_path.rglob("*.orc")
            if p.is_file()
        )

        if explicit_orc:
            return explicit_orc

        part_files = sorted(
            p for p in table_path.rglob("part-*")
            if p.is_file()
        )

        if part_files:
            return part_files

        return sorted(
            p for p in table_path.rglob("*")
            if p.is_file()
            and not p.name.startswith((".", "_"))
        )

    def _first_readable_file(self, table: str) -> Path:
        last_error: Exception | None = None

        for path in self._files(table):
            try:
                orc.ORCFile(str(path))
                return path
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            f"No readable ORC files found for table {table}."
        ) from last_error

    # ------------------------------------------------------------------
    # Arrow helpers
    # ------------------------------------------------------------------

    def _read_file(
        self,
        path: Path,
        columns: Sequence[str] | None = None,
    ) -> pa.Table:
        reader = orc.ORCFile(str(path))
        return reader.read(
            columns=list(columns) if columns else None
        )

    def _query_arrow(
        self,
        arrow_table: pa.Table,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> pd.DataFrame:
        self.connection.register("_swh_arrow", arrow_table)

        try:
            if params:
                return self.connection.execute(
                    sql,
                    list(params),
                ).df()

            return self.connection.execute(sql).df()

        finally:
            try:
                self.connection.unregister("_swh_arrow")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def schema(self, table: str) -> pd.DataFrame:
        path = self._first_readable_file(table)
        reader = orc.ORCFile(str(path))
        arrow_schema = reader.schema

        return pd.DataFrame(
            {
                "column_name": arrow_schema.names,
                "column_type": [
                    str(field.type)
                    for field in arrow_schema
                ],
                "null": [
                    "YES" if field.nullable else "NO"
                    for field in arrow_schema
                ],
            }
        )

    def columns(self, table: str) -> list[str]:
        return self.schema(table)["column_name"].astype(str).tolist()

    def column_type(self, table: str, column: str) -> str:
        schema = self.schema(table)

        row = schema.loc[
            schema["column_name"] == column,
            "column_type",
        ]

        if row.empty:
            raise ValueError(f"Unknown column: {column}")

        return str(row.iloc[0])

    # ------------------------------------------------------------------
    # Basic table operations
    # ------------------------------------------------------------------

    def sample(
        self,
        table: str,
        limit: int = 50,
    ) -> pd.DataFrame:
        limit = max(1, min(int(limit), 1000))

        frames: list[pd.DataFrame] = []
        remaining = limit

        for path in self._files(table):
            try:
                arrow_table = self._read_file(path)
            except Exception:
                continue

            if arrow_table.num_rows == 0:
                continue

            chunk = arrow_table.slice(
                0,
                min(remaining, arrow_table.num_rows),
            ).to_pandas()

            frames.append(chunk)
            remaining -= len(chunk)

            if remaining <= 0:
                break

        if not frames:
            return pd.DataFrame(
                columns=self.columns(table)
            )

        return pd.concat(
            frames,
            ignore_index=True,
        ).head(limit)

    def count(self, table: str) -> int:
        total = 0

        for path in self._files(table):
            try:
                reader = orc.ORCFile(str(path))
                total += int(reader.nrows)
            except Exception:
                continue

        return total

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_rows(
        self,
        table: str,
        column: str,
        operator: str,
        value: Any | None = None,
        limit: int = 100,
        selected_columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:

        if operator not in ALLOWED_OPERATORS:
            raise ValueError("Unsupported filter operator.")

        available = self.columns(table)

        if column not in available:
            raise ValueError("Unknown column.")

        if selected_columns:
            unknown = set(selected_columns) - set(available)

            if unknown:
                raise ValueError(
                    f"Unknown selected columns: {sorted(unknown)}"
                )

            needed_columns = list(
                dict.fromkeys(
                    [*selected_columns, column]
                )
            )

            select_expr = ", ".join(
                quote_identifier(c)
                for c in selected_columns
            )
        else:
            needed_columns = available
            select_expr = "*"

        ident = quote_identifier(column)
        params: list[Any] = []

        if operator == "is_null":
            predicate = f"{ident} IS NULL"

        elif operator == "not_null":
            predicate = f"{ident} IS NOT NULL"

        elif operator == "contains":
            predicate = (
                f"CAST({ident} AS VARCHAR) ILIKE ?"
            )
            params.append(f"%{value}%")

        elif operator == "starts_with":
            predicate = (
                f"CAST({ident} AS VARCHAR) ILIKE ?"
            )
            params.append(f"{value}%")

        else:
            predicate = (
                f"CAST({ident} AS VARCHAR) "
                f"{operator} CAST(? AS VARCHAR)"
            )
            params.append(str(value))

        limit = max(1, min(int(limit), 5000))

        frames: list[pd.DataFrame] = []
        remaining = limit

        for path in self._files(table):
            try:
                arrow_table = self._read_file(
                    path,
                    columns=needed_columns,
                )
            except Exception:
                continue

            sql = f"""
                SELECT {select_expr}
                FROM _swh_arrow
                WHERE {predicate}
                LIMIT {remaining}
            """

            frame = self._query_arrow(
                arrow_table,
                sql,
                params,
            )

            if not frame.empty:
                frames.append(frame)
                remaining -= len(frame)

            if remaining <= 0:
                break

        if not frames:
            return pd.DataFrame(
                columns=selected_columns or available
            )

        return pd.concat(
            frames,
            ignore_index=True,
        ).head(limit)

    # ------------------------------------------------------------------
    # Object lookups
    # ------------------------------------------------------------------

    def lookup_id(
        self,
        table: str,
        object_id: str,
        limit: int = 20,
    ) -> pd.DataFrame:

        if table == "content":
            column = "sha1_git"

        elif table in {
            "revision",
            "release",
            "snapshot",
            "directory",
        }:
            column = "id"

        else:
            raise ValueError(
                f"ID lookup is not defined for table {table}."
            )

        object_id = object_id.strip().lower()

        if (
            len(object_id) != 40
            or any(
                c not in "0123456789abcdef"
                for c in object_id
            )
        ):
            raise ValueError(
                "Object IDs must be 40 hexadecimal characters."
            )

        return self.filter_rows(
            table=table,
            column=column,
            operator="=",
            value=object_id,
            limit=limit,
        )

    def sample_ids(
        self,
        table: str,
        limit: int = 10,
    ) -> list[str]:

        if table == "content":
            column = "sha1_git"

        elif table in {
            "revision",
            "release",
            "snapshot",
            "directory",
        }:
            column = "id"

        else:
            return []

        if (
            not self.has_table(table)
            or column not in self.columns(table)
        ):
            return []

        results: list[str] = []

        for path in self._files(table):
            try:
                arrow_table = self._read_file(
                    path,
                    columns=[column],
                )
            except Exception:
                continue

            series = (
                arrow_table[column]
                .to_pandas()
                .dropna()
                .astype(str)
            )

            for value in series:
                value = value.lower().strip()

                if (
                    len(value) == 40
                    and all(
                        c in "0123456789abcdef"
                        for c in value
                    )
                ):
                    results.append(value)

                if len(results) >= limit:
                    return results

        return results

    # ------------------------------------------------------------------
    # Graph relationships
    # ------------------------------------------------------------------

    def revision_parents(
        self,
        revision_id: str,
    ) -> pd.DataFrame:

        if not self.has_table("revision_history"):
            return pd.DataFrame()

        revision_id = revision_id.strip().lower()

        return self.filter_rows(
            table="revision_history",
            column="id",
            operator="=",
            value=revision_id,
            limit=5000,
            selected_columns=[
                "id",
                "parent_id",
                "parent_rank",
            ],
        )

    def revision_children(
        self,
        revision_id: str,
        limit: int = 100,
    ) -> pd.DataFrame:

        if not self.has_table("revision_history"):
            return pd.DataFrame()

        revision_id = revision_id.strip().lower()

        frame = self.filter_rows(
            table="revision_history",
            column="parent_id",
            operator="=",
            value=revision_id,
            limit=limit,
            selected_columns=[
                "id",
                "parent_id",
                "parent_rank",
            ],
        )

        if not frame.empty:
            frame = frame.rename(
                columns={"id": "child_id"}
            )

        return frame

    def snapshot_branches(
        self,
        snapshot_id: str,
        limit: int = 500,
    ) -> pd.DataFrame:

        if not self.has_table("snapshot_branch"):
            return pd.DataFrame()

        return self.filter_rows(
            table="snapshot_branch",
            column="snapshot_id",
            operator="=",
            value=snapshot_id.strip().lower(),
            limit=limit,
            selected_columns=[
                "snapshot_id",
                "name",
                "target",
                "target_type",
            ],
        )

    def directory_entries(
        self,
        directory_id: str,
        limit: int = 500,
    ) -> pd.DataFrame:

        if not self.has_table("directory_entry"):
            return pd.DataFrame()

        return self.filter_rows(
            table="directory_entry",
            column="directory_id",
            operator="=",
            value=directory_id.strip().lower(),
            limit=limit,
            selected_columns=[
                "directory_id",
                "name",
                "type",
                "target",
                "perms",
            ],
        )

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def revision_activity_by_month(
        self,
        limit_months: int = 120,
    ) -> pd.DataFrame:

        if not self.has_table("revision"):
            return pd.DataFrame()

        if "date" not in self.columns("revision"):
            return pd.DataFrame()

        pieces: list[pd.DataFrame] = []

        for path in self._files("revision"):
            try:
                arrow_table = self._read_file(
                    path,
                    columns=["date"],
                )
            except Exception:
                continue

            frame = self._query_arrow(
                arrow_table,
                """
                SELECT
                    date_trunc('month', date) AS month,
                    COUNT(*) AS revisions
                FROM _swh_arrow
                WHERE date IS NOT NULL
                GROUP BY 1
                """
            )

            if not frame.empty:
                pieces.append(frame)

        if not pieces:
            return pd.DataFrame(
                columns=["month", "revisions"]
            )

        result = pd.concat(
            pieces,
            ignore_index=True,
        )

        result = (
            result.groupby(
                "month",
                as_index=False,
            )["revisions"]
            .sum()
            .sort_values("month")
        )

        return result.tail(
            max(
                1,
                min(int(limit_months), 1200),
            )
        )

    def merge_distribution(
        self,
    ) -> pd.DataFrame:

        if not self.has_table("revision_history"):
            return pd.DataFrame()

        parent_counts: Counter[str] = Counter()

        for path in self._files("revision_history"):
            try:
                arrow_table = self._read_file(
                    path,
                    columns=["id"],
                )
            except Exception:
                continue

            ids = (
                arrow_table["id"]
                .to_pandas()
                .dropna()
                .astype(str)
            )

            parent_counts.update(ids)

        if not parent_counts:
            return pd.DataFrame(
                columns=[
                    "parent_count",
                    "revisions",
                ]
            )

        distribution = Counter(
            parent_counts.values()
        )

        return pd.DataFrame(
            [
                {
                    "parent_count": parent_count,
                    "revisions": revision_count,
                }
                for parent_count, revision_count
                in sorted(distribution.items())
            ]
        )

    def content_size_summary(
        self,
    ) -> pd.DataFrame:

        if not self.has_table("content"):
            return pd.DataFrame()

        if "length" not in self.columns("content"):
            return pd.DataFrame()

        lengths: list[pd.Series] = []

        for path in self._files("content"):
            try:
                arrow_table = self._read_file(
                    path,
                    columns=["length"],
                )
            except Exception:
                continue

            series = pd.to_numeric(
                arrow_table["length"].to_pandas(),
                errors="coerce",
            ).dropna()

            if not series.empty:
                lengths.append(series)

        if not lengths:
            return pd.DataFrame()

        values = pd.concat(
            lengths,
            ignore_index=True,
        )

        return pd.DataFrame(
            [
                {
                    "objects": int(values.count()),
                    "mean_bytes": float(values.mean()),
                    "median_bytes": float(values.median()),
                    "max_bytes": float(values.max()),
                    "total_bytes": float(values.sum()),
                }
            ]
        )