# Software Heritage Research Explorer

Research tools for working with Software Heritage graph data.

Built with Python, DuckDB, and Streamlit.

[Open the app](https://software-heritage-research-explorer.streamlit.app/)

## Current work

The project is being used to explore Software Heritage data and revision histories, including:

* origins, snapshots, branches, and revisions
* commit and revision history
* relationships between archived software objects
* archive-level trends and project activity

The current focus is on tracing projects from an origin through their revision history and using that history for research analysis.

## Data

The application works with Software Heritage graph exports in ORC format.

Software Heritage documentation:
https://docs.softwareheritage.org/

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Software Heritage references

- Documentation: https://docs.softwareheritage.org/
- Graph datasets: https://docs.softwareheritage.org/devel/swh-dataset/graph/dataset.html
- Graph relational schema: https://docs.softwareheritage.org/devel/swh-export/graph/schema.html
- SWHID specification: https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html
- Archive: https://archive.softwareheritage.org/

## Status

Research prototype. The immediate roadmap is documented in [`docs/ROADMAP.md`](docs/ROADMAP.md), including origin-to-snapshot traversal, recursive directory exploration, richer revision-topology analysis, and integration fixtures.

## License

MIT. See [`LICENSE`](LICENSE).
