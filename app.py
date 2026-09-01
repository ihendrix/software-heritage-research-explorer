from __future__ import annotations

import streamlit as st

from src.catalog import TABLE_DESCRIPTIONS
from src.config import APP_TITLE
from src.ui import connected_engine

st.set_page_config(page_title=APP_TITLE, page_icon="🗃️", layout="wide")

st.title(APP_TITLE)
st.caption("A local-first research interface for exploring Software Heritage graph exports and testing evidence-grounded AI workflows.")

engine = connected_engine()

if engine is not None and engine.tables:
    c1, c2, c3 = st.columns(3)
    c1.metric("Discovered tables", len(engine.tables))
    c2.metric("Known graph tables", len(set(engine.tables) & set(TABLE_DESCRIPTIONS)))
    c3.metric("Query engine", "DuckDB")
    st.success("Dataset connected. Use the pages in the sidebar to inspect tables, traverse relationships, analyze archive structure, or build an evidence-grounded research brief.")
else:
    st.info("The repository intentionally does not bundle the large Software Heritage ORC export. Add a local dataset path in the sidebar. The SWHID Inspector remains usable without local data.")

st.subheader("What this prototype demonstrates")
st.markdown(
    """
- **Archive-aware exploration:** inspect ORC schemas and query records without loading entire tables into memory.
- **Graph reasoning:** traverse revision parents/children, snapshot branches, and directory entries instead of treating exports as disconnected files.
- **SWHID literacy:** parse Software Heritage persistent identifiers and map them to local archive tables.
- **Evidence-grounded AI:** optionally synthesize only the structured evidence retrieved from the archive rather than asking a model to improvise over raw data.
- **Local-first design:** the archive remains authoritative; AI is an analysis layer, not a replacement for deterministic queries.
"""
)

st.subheader("Archive model")
mermaid = """
graph LR
    O[Origin] --> V[Origin visit]
    V --> S[Snapshot]
    S --> B[Snapshot branch]
    B --> R[Revision]
    R --> P[Parent revision]
    R --> D[Directory]
    D --> E[Directory entry]
    E --> C[Content / subdirectory]
"""
st.code(mermaid, language="text")

st.caption("Software Heritage exports encode the archive's Merkle DAG as relational tables. This UI focuses on the relationships among those tables, not only row counts.")
