from __future__ import annotations

import streamlit as st

from src.ui import require_engine

st.set_page_config(page_title="Archive Analytics", page_icon="📊", layout="wide")
st.title("Archive Analytics")
st.caption("A small set of reproducible analytical views derived directly from local archive tables.")

engine = require_engine()

st.subheader("Revision activity")
try:
    activity = engine.revision_activity_by_month()
    if activity.empty:
        st.info("Revision dates are unavailable in this connected export.")
    else:
        st.line_chart(activity.set_index("month")["revisions"])
        st.dataframe(activity.tail(24), use_container_width=True, hide_index=True)
except Exception as exc:
    st.warning(f"Revision activity unavailable: {exc}")

st.subheader("Revision parent-count distribution")
try:
    merge_dist = engine.merge_distribution()
    if merge_dist.empty:
        st.info("revision_history is unavailable.")
    else:
        st.bar_chart(merge_dist.set_index("parent_count")["revisions"])
        st.caption("Two parents generally indicate a merge revision; three or more can represent octopus-style merges.")
except Exception as exc:
    st.warning(f"Merge analysis unavailable: {exc}")

st.subheader("Content-size summary")
try:
    content = engine.content_size_summary()
    if content.empty:
        st.info("Content length data is unavailable.")
    else:
        row = content.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Content objects", f"{int(row['objects']):,}")
        c2.metric("Median bytes", f"{float(row['median_bytes']):,.0f}")
        c3.metric("Mean bytes", f"{float(row['mean_bytes']):,.0f}")
        c4.metric("Max bytes", f"{float(row['max_bytes']):,.0f}")
except Exception as exc:
    st.warning(f"Content analysis unavailable: {exc}")
