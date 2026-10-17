# PDF Report Generator

A small FastAPI service that generates downloadable PDF sales reports from a
SQLite database. Reports include order and revenue totals, the top five
products by revenue, and the complete order list. The sample database can be
populated with generated orders using `seed.py`.

## Setup and run


```powershell
uv init 
uv add fastapi uvicorn playwright
uv run playwright install chromium
uv run python seed.py
uv run uvicorn main:app --reload
```

The service runs at `http://127.0.0.1:8000`. Interactive API documentation is
available at `http://127.0.0.1:8000/docs`.

## API

- `GET /health` — check that the service is running.
- `POST /reports` — generate a report. Send `{"force": true}` to create a
  fresh report even if one was already generated today.
- `GET /reports/{report_id}` — get report metadata.
- `GET /reports/{report_id}/file` — download the PDF.

## How it was created with `uv`

`uv init` creates the minimal project configuration without replacing
the existing Python files. `uv add` records FastAPI, Uvicorn, and Playwright
as project dependencies. Playwright's Chromium browser is installed separately
because it is needed to render the report HTML as a PDF. `uv run` runs each
command in the project's managed environment, creating/synchronizing it as
needed.
