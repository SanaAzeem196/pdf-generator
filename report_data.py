import json
import os
import sqlite3

# Anchor to this script's own directory so it always finds the same
# report.db that seed.py created, regardless of your working directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "report.db")


def getReportData():
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        # 1. Total orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        # 2. Total revenue
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM orders")
        total_revenue = round(cursor.fetchone()[0], 2)

        # 3. Top 5 products by revenue. Group all orders belonging to the same product, add their amounts together, sort products from highest revenue to lowest, and give me the top 5."
        cursor.execute("""
            SELECT product, SUM(amount) AS revenue
            FROM orders
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
        """)
        top_products = [
            {"product": product, "revenue": round(revenue, 2)}
            for product, revenue in cursor.fetchall()
        ]

        # 4. Orders per day for the last 7 days
        # Note: date('now', ...) is UTC-based, while created_at was seeded
        # using local dates in seed.py. If you're in a timezone far from
        # UTC, day boundaries may be off by one near midnight.
        cursor.execute("""
            SELECT created_at, COUNT(*) AS order_count
            FROM orders
            WHERE created_at >= date('now', '-6 days')
            GROUP BY created_at
            ORDER BY created_at
        """)
        orders_per_day = [
            {"date": created_at, "order_count": order_count}
            for created_at, order_count in cursor.fetchall()
        ]

    connection.close()
# valid json requires double quotes. 
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_products": top_products,
        "orders_per_day": orders_per_day,
    }


if __name__ == "__main__":
    report = getReportData()
    print(json.dumps(report, indent=2))