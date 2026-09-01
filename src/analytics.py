from __future__ import annotations

import pandas as pd


def summarize_revision_relationships(parents: pd.DataFrame, children: pd.DataFrame) -> dict[str, int]:
    return {
        "parent_count": int(len(parents)),
        "child_count": int(len(children)),
        "is_merge": int(len(parents) >= 2),
    }


def summarize_snapshot(branches: pd.DataFrame) -> pd.DataFrame:
    if branches.empty or "target_type" not in branches.columns:
        return pd.DataFrame(columns=["target_type", "branches"])
    return (
        branches.groupby("target_type", dropna=False)
        .size()
        .reset_index(name="branches")
        .sort_values("branches", ascending=False)
    )


def evidence_markdown(title: str, frames: dict[str, pd.DataFrame]) -> str:
    parts = [f"# {title}"]
    for name, frame in frames.items():
        parts.append(f"\n## {name}")
        if frame.empty:
            parts.append("No rows returned.")
        else:
            parts.append(frame.head(50).to_markdown(index=False))
    return "\n".join(parts)
