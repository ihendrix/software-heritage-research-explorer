from __future__ import annotations

from pathlib import Path
import streamlit as st

from .config import DEFAULT_DATASET_PATH
from .query_engine import SWHQueryEngine


def dataset_controls() -> Path | None:
    st.sidebar.header("Dataset")
    default = st.session_state.get("dataset_path", DEFAULT_DATASET_PATH)
    value = st.sidebar.text_input(
        "Local ORC dataset path",
        value=default,
        placeholder="/path/to/software-heritage/orc",
        help="Point this at the directory whose children are Software Heritage ORC tables.",
    )
    st.session_state["dataset_path"] = value
    if not value:
        st.sidebar.info("No local dataset connected. Documentation and SWHID parsing still work.")
        return None
    path = Path(value).expanduser()
    if not path.exists():
        st.sidebar.error("Dataset path does not exist.")
        return None
    if not path.is_dir():
        st.sidebar.error("Dataset path must be a directory.")
        return None
    return path.resolve()


@st.cache_resource(show_spinner=False)
def get_engine(dataset_path: str) -> SWHQueryEngine:
    return SWHQueryEngine(dataset_path)


def connected_engine() -> SWHQueryEngine | None:
    path = dataset_controls()
    if path is None:
        return None
    try:
        engine = get_engine(str(path))
    except Exception as exc:
        st.sidebar.error(f"Could not initialize DuckDB: {exc}")
        return None
    if not engine.tables:
        st.sidebar.warning("No ORC-backed tables discovered under this path.")
        return engine
    st.sidebar.success(f"Connected: {len(engine.tables)} table(s)")
    return engine


def require_engine() -> SWHQueryEngine:
    engine = connected_engine()
    if engine is None or not engine.tables:
        st.info("Connect a local Software Heritage ORC export from the sidebar to use this page.")
        st.stop()
    return engine


def bytes_to_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
