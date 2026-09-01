# Design Decisions

## 1. Treat the export as a graph, not a folder of tables

Software Heritage's graph export encodes a Merkle DAG using relational tables. The first version of this project inspected tables independently. Version 2 adds explicit traversal for revision ancestry, snapshot branches, and directory entries so the UI reflects the archive's actual structure.

## 2. Keep the dataset local

The repository does not redistribute Software Heritage exports. Users point the application at an existing ORC export. This keeps the GitHub repository lightweight and avoids pretending a teaser dataset is part of the application itself.

## 3. No arbitrary SQL box

The UI exposes constrained filters and pre-defined graph queries. Table and column names are validated against the connected export, and values are bound as parameters. This is easier to reason about than accepting arbitrary SQL from the browser.

## 4. SWHIDs are first-class objects

The SWHID Inspector parses version-1 core identifiers, maps their object type to a local graph table, and constructs the canonical Software Heritage archive URL. This makes identifiers part of the workflow rather than an afterthought.

## 5. AI is downstream of retrieval

The LLM receives only bounded structured evidence selected by deterministic code. The application always exposes those evidence frames. If no API key is configured, the page still works as a deterministic evidence builder.

## 6. Prefer depth over feature count

This prototype intentionally implements a few archive-native research workflows rather than a large collection of shallow AI buttons. Future work should add new workflows only when the retrieval/evidence path is well defined.
