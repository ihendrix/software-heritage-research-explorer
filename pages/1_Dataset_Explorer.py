from __future__ import annotations

import streamlit as st

from src.catalog import TABLE_DESCRIPTIONS
from src.ui import require_engine

st.set_page_config(page_title="Dataset Explorer", page_icon="🔎", layout="wide")
st.title("Dataset Explorer")
st.caption(
    "Inspect schemas, preview records, and run constrained queries over Software Heritage ORC exports using PyArrow and DuckDB."
)

engine = require_engine()
table = st.selectbox("Table", engine.tables)
st.info(TABLE_DESCRIPTIONS.get(table, "Dataset table."))

schema = engine.schema(table)
st.subheader("Schema")
st.dataframe(schema, use_container_width=True, hide_index=True)

cols = engine.columns(table)
with st.expander("Filtered query", expanded=True):
    selected_columns = st.multiselect("Columns to return", cols, default=cols[: min(8, len(cols))])
    c1, c2, c3 = st.columns([2, 1, 2])
    column = c1.selectbox("Filter column", cols)
    operator = c2.selectbox("Operator", ["=", "!=", "contains", "starts_with", ">", ">=", "<", "<=", "is_null", "not_null"])
    value = c3.text_input("Value", disabled=operator in {"is_null", "not_null"})
    limit = st.slider("Row limit", 10, 1000, 100, 10)
    run = st.button("Run query", type="primary")

if run:
    try:
        result = engine.filter_rows(
            table,
            column,
            operator,
            None if operator in {"is_null", "not_null"} else value,
            limit=limit,
            selected_columns=selected_columns or None,
        )
        st.session_state["last_query_result"] = result
    except Exception as exc:
        st.error(str(exc))

if "last_query_result" in st.session_state:
    result = st.session_state["last_query_result"]
    st.subheader("Results")
    st.dataframe(result, use_container_width=True)
    st.download_button("Download CSV", result.to_csv(index=False).encode("utf-8"), "swh_query.csv", "text/csv")
else:
    st.subheader("Preview")
    try:
        st.dataframe(engine.sample(table, 50), use_container_width=True)
    except Exception as exc:
        st.warning(f"Preview failed: {exc}")
