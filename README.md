# Excel Viewer

A sleek, dark glass-morphism Excel viewer built with **FastHTML + HTMX + pandas**. Upload spreadsheets, filter rows, browse and inspect data in a polished UI.

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
- 🌙 **Dark glass-morphism** UI — easy on the eyes

---

## Troubleshooting

- **"Address already in use"** — another instance is running on port 8765. Find and kill it:
  ```bash
  lsof -i :8765 | grep LISTEN | awk '{print $2}' | xargs kill
  ```
- **Missing packages** — always run `pip install -r requirements.txt` inside the `fhtml` env.
- **`conda: command not found`** — ensure Miniconda/Anaconda is in your `$PATH`.