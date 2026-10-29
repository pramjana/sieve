# Sieve

A sleek, dark glass-morphism spreadsheet slicer built with **FastHTML + HTMX + pandas**. Upload spreadsheets, slice and dice rows with search and column filters, inspect detail views, save views, and export the filtered result as CSV or Excel.

---

## Quick Start

```bash
# 1. Activate the conda environment
conda activate fhtml

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

The server starts at **http://localhost:8765**.

---

## Prerequisites

- [**Python**](https://www.python.org/) ≥ 3.10
- [**Conda**](https://conda.io/) (Miniconda or Anaconda)
- Conda environment named **`fhtml`**

### Setting up the `fhtml` environment (first time)

```bash
conda create -n fhtml python=3.11 -y
conda activate fhtml
pip install -r requirements.txt
```

---

## Dependencies

| Package       | Version | Purpose                          |
|---------------|---------|----------------------------------|
| `python-fasthtml` | ≥ 0.14.0 | Web framework (FastAPI + HTMX) |
| `pandas`      | ≥ 2.0   | Spreadsheet data manipulation    |
| `openpyxl`    | ≥ 3.1   | Excel (.xlsx) file parsing       |

---

## Features

- 📤 **Upload** `.xlsx` files with drag-and-drop
- 🔍 **Filter** rows with search and column-specific filters
- 📊 **Browse** paginated, sortable tables
- 🧠 **Inspect** individual rows with detail views
- 🌗 **"Ink & Paper" themes** — elegant dark and light palettes with a
  persisted toggle (respects your OS preference on first visit)

[⛔90d9e972-a7a5-4a61-a81a-36107f8b4435]
## Performance & Limits

- **Single process by design.** All viewer state lives in one module-global
  dict, so never run `uvicorn --workers > 1` — each worker would hold a
  different half of the session. Parse/render run on Starlette's threadpool,
  so the UI stays responsive while a workbook loads.
- `MAX_FILE_SIZE` = 100 MB (rejected before the body is buffered).
- `MAX_ROWS` = 500 row cards rendered at once; narrow your search to see more.
- `DC_DEFAULT` = 10 detail columns auto-selected on load; check more chips if
  you want them in the detail pane.
- **Wide sheets** (hundreds of columns) stay snappy: the sidebar renders
  collapsed filter-group stubs and fetches each group's controls lazily on
  expand (`GET /filter/{idx}`), instead of shipping thousands of checkboxes
  in every page swap.

---

## Troubleshooting

- **"Address already in use"** — another instance is running on port 8765. Find and kill it:
  ```bash
  lsof -i :8765 | grep LISTEN | awk '{print $2}' | xargs kill
  ```
- **Missing packages** — always run `pip install -r requirements.txt` inside the `fhtml` env.
- **`conda: command not found`** — ensure Miniconda/Anaconda is in your `$PATH`.