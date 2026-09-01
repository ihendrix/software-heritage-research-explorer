# AI Research Layer

The AI page is an experiment in **grounded archive analysis**, not a generic chatbot.

## Workflow

1. The user selects a bounded research workflow (revision, snapshot, directory, or aggregate revision activity).
2. Deterministic DuckDB queries retrieve the relevant records and relationships.
3. Those DataFrames are converted to a bounded JSON evidence payload.
4. If `OPENAI_API_KEY` is configured, the Responses API receives the research question plus that evidence payload.
5. The generated brief must distinguish findings, evidence, interpretation, and limitations.
6. The exact source DataFrames remain visible below the generated text.

## Why this design

A model should not be asked to infer the structure of a multi-gigabyte archive export from an arbitrary sample. It is better used after the application has retrieved the exact revision parents, snapshot branches, directory entries, or aggregate statistics relevant to the question.

## Current limitations

- The prototype does not implement autonomous arbitrary SQL generation.
- It does not claim that a local teaser export represents the whole archive.
- The model cannot establish facts that are absent from the evidence bundle.
- Model output is analytical commentary and can still be wrong; the displayed archive records are the source of truth.
