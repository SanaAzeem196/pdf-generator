import os
import sqlite3
from datetime import date

from playwright.sync_api import sync_playwright

from report_data import getReportData

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "report.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
PDF_PATH = os.path.join(REPORTS_DIR, "test.pdf")


def build_html(report):
    today = date.today().isoformat()

    # report["top_products"] is a list of dicts, e.g.
    # {"product": "Laptop", "revenue": 1234.5} — not tuples, so unpack
    # each item's values by key rather than as (product, revenue).
    top_products_rows = ""
    for item in report["top_products"]:
        top_products_rows += f"""
            <tr>
                <td>{item['product']}</td>
                <td>{item['revenue']:.2f}</td>
            </tr>
        """

    # timeout=30: same reasoning as report_data.py — wait for main.py's
    # write lock to release instead of failing fast.
    with sqlite3.connect(DATABASE, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, customer, product, amount, created_at
            FROM orders
            ORDER BY created_at DESC, id DESC
        """)
        orders = cursor.fetchall()

    order_rows = ""
    for order_id, customer, product, amount, created_at in orders:
        order_rows += f"""
            <tr>
                <td>{order_id}</td>
                <td>{customer}</td>
                <td>{product}</td>
                <td>{amount:.2f}</td>
                <td>{created_at}</td>
            </tr>
        """

    # Note the doubled-up {{ }} inside the <style> tags below:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Shop Sales Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #222;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            .date {{
                color: #666;
                margin-bottom: 30px;
            }}

            .summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}

            .card {{
                border: 1px solid #ddd;
                padding: 20px;
                width: 200px;
            }}

            .card-title {{
                font-size: 14px;
                color: #666;
            }}

            .card-value {{
                font-size: 24px;
                font-weight: bold;
                margin-top: 8px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                margin-bottom: 30px;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background: #f2f2f2;
            }}

            thead {{
                display: table-header-group;
            }}

            tr {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            .section {{
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <h1>Shop Sales Report</h1>
        <div class="date">Report Date: {today}</div>

        <div class="summary">
            <div class="card">
                <div class="card-title">Total Orders</div>
                <div class="card-value">{report["total_orders"]}</div>
            </div>
            <div class="card">
                <div class="card-title">Total Revenue</div>
                <div class="card-value">{report["total_revenue"]:.2f}</div>
            </div>
        </div>

        <div class="section">
            <h2>Top 5 Products by Revenue</h2>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Revenue</th>
                    </tr>
                </thead>
                <tbody>
                    {top_products_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>All Orders</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Customer</th>
                        <th>Product</th>
                        <th>Amount</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    {order_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html


def create_pdf(pdf_path):
    dir_name = os.path.dirname(pdf_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    report = getReportData()
    html = build_html(report)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(html)
            page.pdf(
                path=pdf_path,
                format="A4",
                print_background=True
            )
            print(f"PDF successfully generated at: {pdf_path}")
        finally:
            browser.close()


if __name__ == "__main__":
    create_pdf(PDF_PATH)