from __future__ import annotations

import streamlit as st

from src.analytics import summarize_revision_relationships, summarize_snapshot
from src.ui import require_engine

st.set_page_config(page_title="Graph Relationships", page_icon="🕸️", layout="wide")
st.title("Graph Relationships")
st.caption("Traverse deterministic relationships represented by Software Heritage graph-export tables.")

engine = require_engine()
mode = st.radio("Relationship", ["Revision ancestry", "Snapshot branches", "Directory entries"], horizontal=True)

if mode == "Revision ancestry":
    examples = engine.sample_ids("revision", 8)
    if examples:
        with st.expander("Choose an example revision", expanded=False):
            chosen = st.selectbox("Available revision IDs", examples, key="revision_example")
            if st.button("Use this revision"):
                st.session_state["revision_id"] = chosen
    revision_id = st.text_input(
        "Revision ID",
        value=st.session_state.get("revision_id", ""),
        placeholder="40-character hexadecimal revision identifier",
    )
    if st.button("Trace revision", type="primary") and revision_id:
        revision_id = revision_id.strip().lower()
        try:
            revision = engine.lookup_id("revision", revision_id) if engine.has_table("revision") else None
            parents = engine.revision_parents(revision_id)
            children = engine.revision_children(revision_id)
            summary = summarize_revision_relationships(parents, children)
            c1, c2, c3 = st.columns(3)
            c1.metric("Parents", summary["parent_count"])
            c2.metric("Children", summary["child_count"])
            c3.metric("Merge revision", "Yes" if summary["is_merge"] else "No")
            if revision is not None:
                st.subheader("Revision")
                st.dataframe(revision, use_container_width=True)
            st.subheader("Parents")
            st.dataframe(parents, use_container_width=True)
            st.subheader("Children")
            st.dataframe(children, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

elif mode == "Snapshot branches":
    examples = engine.sample_ids("snapshot", 8)
    if examples:
        with st.expander("Choose an example snapshot", expanded=False):
            chosen = st.selectbox("Available snapshot IDs", examples, key="snapshot_example")
            if st.button("Use this snapshot"):
                st.session_state["snapshot_id"] = chosen
    snapshot_id = st.text_input(
        "Snapshot ID",
        value=st.session_state.get("snapshot_id", ""),
        placeholder="40-character hexadecimal snapshot identifier",
    )
    if st.button("Inspect snapshot", type="primary") and snapshot_id:
        try:
            branches = engine.snapshot_branches(snapshot_id.strip().lower())
            st.metric("Branches returned", len(branches))
            breakdown = summarize_snapshot(branches)
            if not breakdown.empty:
                st.bar_chart(breakdown.set_index("target_type")["branches"])
            st.dataframe(branches, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

else:
    examples = engine.sample_ids("directory", 8)
    if examples:
        with st.expander("Choose an example directory", expanded=False):
            chosen = st.selectbox("Available directory IDs", examples, key="directory_example")
            if st.button("Use this directory"):
                st.session_state["directory_id"] = chosen
    directory_id = st.text_input(
        "Directory ID",
        value=st.session_state.get("directory_id", ""),
        placeholder="40-character hexadecimal directory identifier",
    )
    if st.button("Inspect directory", type="primary") and directory_id:
        try:
            entries = engine.directory_entries(directory_id.strip().lower())
            st.metric("Entries returned", len(entries))
            if not entries.empty and "type" in entries.columns:
                st.bar_chart(entries["type"].value_counts())
            st.dataframe(entries, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))
