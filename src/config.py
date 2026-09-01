from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "Software Heritage Research Explorer"
DEFAULT_DATASET_PATH = os.getenv("SWH_DATASET_PATH", "")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
SUMMARY_CSV = Path(__file__).resolve().parents[1] / "table_summary.csv"


def normalized_dataset_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    try:
        return path.resolve()
    except OSError:
        return path
