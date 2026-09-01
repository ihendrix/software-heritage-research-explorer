from __future__ import annotations

import streamlit as st

from src.swhid import parse_swhid
from src.ui import connected_engine

st.set_page_config(page_title="SWHID Inspector", page_icon="🔗", layout="wide")
st.title("SWHID Inspector")
st.caption("Parse a Software Heritage persistent identifier, connect it to the archive data model, and optionally resolve it against the local ORC export.")

engine = connected_engine()

if engine is not None and engine.has_table("revision"):
    try:
        examples = engine.sample_ids("revision", 5)
    except Exception:
        examples = []
else:
    examples = []

if examples:
    example_swhid = f"swh:1:rev:{examples[0]}"
    if st.button("Load an example SWHID"):
        st.session_state["swhid_value"] = example_swhid

value = st.text_input(
    "SWHID",
    value=st.session_state.get("swhid_value", ""),
    placeholder="swh:1:rev:0123456789abcdef0123456789abcdef01234567",
)

if value:
    try:
        parsed = parse_swhid(value)
        c1, c2, c3 = st.columns(3)
        c1.metric("Scheme version", parsed.version)
        c2.metric("Object type", parsed.table)
        c3.metric("Object ID", parsed.object_id[:12] + "…")
        st.code(parsed.core)
        st.link_button("Open in Software Heritage", parsed.archive_url)
        if parsed.qualifiers:
            st.write("Qualifiers:", parsed.qualifiers)

        if engine is not None and engine.has_table(parsed.table):
            st.subheader("Local dataset match")
            try:
                match = engine.lookup_id(parsed.table, parsed.object_id)
                if match.empty:
                    st.info("No matching object was found in the connected local export.")
                else:
                    st.dataframe(match, use_container_width=True)
            except Exception as exc:
                st.warning(f"Local lookup unavailable: {exc}")
        elif engine is not None:
            st.info(f"The connected export does not contain a {parsed.table!r} table.")
    except ValueError as exc:
        st.error(str(exc))
