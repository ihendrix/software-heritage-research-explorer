from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd

from .config import DEFAULT_MODEL

SYSTEM_INSTRUCTIONS = """You are an evidence-grounded research assistant for the Software Heritage archive.
Use only the structured evidence supplied in the prompt. Distinguish observations from interpretations.
Never invent repository history, people, objects, or relationships. If evidence is insufficient, say so.
When referring to an archive object, preserve its identifier exactly. Return concise Markdown with sections:
Finding, Evidence, Interpretation, Limitations."""


def frame_records(frame: pd.DataFrame, limit: int = 100) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    safe = frame.head(limit).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(_json_safe)
    return safe.to_dict(orient="records")


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def build_evidence_payload(question: str, evidence: dict[str, pd.DataFrame]) -> str:
    payload = {
        "question": question,
        "evidence": {name: frame_records(frame) for name, frame in evidence.items()},
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def ai_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def synthesize_with_openai(question: str, evidence: dict[str, pd.DataFrame], model: str | None = None) -> str:
    if not ai_available():
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The optional openai package is not installed.") from exc

    client = OpenAI()
    response = client.responses.create(
        model=model or DEFAULT_MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=build_evidence_payload(question, evidence),
    )
    return response.output_text


def deterministic_brief(question: str, evidence: dict[str, pd.DataFrame]) -> str:
    lines = ["## Finding", f"Prepared an evidence bundle for: **{question}**", "", "## Evidence"]
    for name, frame in evidence.items():
        lines.append(f"- **{name}:** {len(frame):,} row(s) returned")
    lines.extend([
        "",
        "## Interpretation",
        "AI synthesis is disabled, so no model-generated interpretation was produced. The tables below remain the authoritative evidence.",
        "",
        "## Limitations",
        "This result is limited to the local Software Heritage dataset connected to the explorer.",
    ])
    return "\n".join(lines)
