import os
import sqlite3
import uuid

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from report_pdf import create_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "report.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

app = FastAPI()


class ReportRequest(BaseModel):
    force: bool = False


def init_reports_table():
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


init_reports_table()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports")
def generate_report(request: ReportRequest):
    # Use a longer SQLite timeout so a second rapid request
    # waits for the first request to finish instead of failing
    # with "database is locked".
    connection = sqlite3.connect(DATABASE, timeout=30)
    cursor = connection.cursor()

    try:
        # BEGIN IMMEDIATE obtains a write lock.
        # This prevents two rapid requests from both passing
        # the duplicate check at the same time. report_data.py and
        # report_pdf.py now also connect with timeout=30, so they wait
        # for this lock to release instead of erroring out while
        # create_pdf() is running below.
        connection.execute("BEGIN IMMEDIATE")

        # Stage 5 duplicate check:
        # If a report was already generated today and force=False,
        # return that existing report instead of creating another.
        if not request.force:
            cursor.execute("""
                SELECT id, path
                FROM reports
                WHERE date(created_at) = date('now')
                ORDER BY created_at DESC
                LIMIT 1
            """)

            existing_report = cursor.fetchone()

            if existing_report is not None:
                connection.commit()

                return JSONResponse(
                    status_code=200,
                    content={
                        "id": existing_report[0],
                        "file": f"/reports/{existing_report[0]}/file"
                    }
                )

        # No report exists today, or force=True.
        # Create a new report.
        report_id = str(uuid.uuid4())

        pdf_path = os.path.join(
            REPORTS_DIR,
            f"{report_id}.pdf"
        )

        create_pdf(pdf_path)

        # Store the generated report in the database.
        cursor.execute("""
            INSERT INTO reports (id, path, created_at)
            VALUES (?, ?, datetime('now'))
        """, (report_id, pdf_path))

        connection.commit()

        return JSONResponse(
            status_code=201,
            content={
                "id": report_id,
                "file": f"/reports/{report_id}/file"
            }
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


@app.get("/reports/{report_id}")
def get_report(report_id: str):
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, path, created_at
            FROM reports
            WHERE id = ?
        """, (report_id,))

        report = cursor.fetchone()

    if report is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Report not found"}
        )

    return {
        "id": report[0],
        "path": report[1],
        "created_at": report[2],
        "file": f"/reports/{report[0]}/file"
    }


@app.get("/reports/{report_id}/file")
def download_report(report_id: str):
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT path
            FROM reports
            WHERE id = ?
        """, (report_id,))

        report = cursor.fetchone()

    if report is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Report not found"}
        )

    pdf_path = report[0]

    if not os.path.isfile(pdf_path):
        return JSONResponse(
            status_code=404,
            content={"detail": "Report file not found"}
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"report-{report_id}.pdf"
    )