from __future__ import annotations

import streamlit as st

from src.config import DEFAULT_MODEL
from src.research import ai_available, deterministic_brief, synthesize_with_openai
from src.ui import require_engine

st.set_page_config(page_title="AI Research", page_icon="🧠", layout="wide")
st.title("Evidence-Grounded AI Research")
st.caption("Deterministic archive queries build an evidence bundle first. AI, when enabled, synthesizes only that retrieved evidence.")

engine = require_engine()
mode = st.selectbox(
    "Research workflow",
    ["Explain a revision", "Explain a snapshot", "Explain a directory", "Analyze revision activity"],
)
question = st.text_area(
    "Research question",
    placeholder="What is unusual or notable about this object based on the evidence available here?",
)

identifier = None
if mode != "Analyze revision activity":
    table_for_mode = {
        "Explain a revision": "revision",
        "Explain a snapshot": "snapshot",
        "Explain a directory": "directory",
    }[mode]
    try:
        examples = engine.sample_ids(table_for_mode, 8)
    except Exception:
        examples = []
    if examples:
        with st.expander("Choose an object from this dataset", expanded=False):
            chosen = st.selectbox("Example object ID", examples, key=f"ai_{table_for_mode}_example")
            if st.button("Use this object"):
                st.session_state["ai_object_id"] = chosen
    identifier = st.text_input(
        "Object ID",
        value=st.session_state.get("ai_object_id", ""),
        placeholder="40-character hexadecimal identifier",
    )

model = st.text_input("OpenAI model", value=DEFAULT_MODEL)

if ai_available():
    st.success("OpenAI API key detected. AI synthesis is enabled.")
else:
    st.info("AI is optional. Without an API key, the page still constructs and displays the deterministic evidence bundle.")

if st.button("Build research brief", type="primary"):
    evidence = {}
    try:
        if mode == "Explain a revision":
            rid = (identifier or "").strip().lower()
            if not rid:
                raise ValueError("Choose or enter a revision ID first.")
            evidence["revision"] = engine.lookup_id("revision", rid)
            evidence["parents"] = engine.revision_parents(rid)
            evidence["children"] = engine.revision_children(rid)
        elif mode == "Explain a snapshot":
            sid = (identifier or "").strip().lower()
            if not sid:
                raise ValueError("Choose or enter a snapshot ID first.")
            evidence["snapshot"] = engine.lookup_id("snapshot", sid)
            evidence["branches"] = engine.snapshot_branches(sid)
        elif mode == "Explain a directory":
            did = (identifier or "").strip().lower()
            if not did:
                raise ValueError("Choose or enter a directory ID first.")
            evidence["directory"] = engine.lookup_id("directory", did)
            evidence["entries"] = engine.directory_entries(did)
        else:
            evidence["revision_activity_by_month"] = engine.revision_activity_by_month()
            evidence["parent_count_distribution"] = engine.merge_distribution()

        prompt = question.strip() or f"Summarize the evidence for workflow: {mode}."

        if ai_available():
            with st.spinner("Synthesizing retrieved evidence…"):
                brief = synthesize_with_openai(prompt, evidence, model=model)
        else:
            brief = deterministic_brief(prompt, evidence)

        st.markdown(brief)
        st.subheader("Evidence bundle")
        for name, frame in evidence.items():
            with st.expander(f"{name} — {len(frame):,} row(s)", expanded=False):
                st.dataframe(frame, use_container_width=True)
    except Exception as exc:
        st.error(str(exc))
