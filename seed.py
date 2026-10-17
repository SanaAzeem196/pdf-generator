import os
import random
import sqlite3
from datetime import date, timedelta

# Anchor to this script's own directory so every file in the project
# resolves to the same report.db, no matter what directory you run from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "report.db")

PRODUCTS = [
    "Laptop",
    "Keyboard",
    "Mouse",
    "Monitor",
    "Headphones",
    "Webcam",
]

CUSTOMERS = [
    "Ali",
    "Ahmed",
    "Sara",
    "Ayesha",
    "Usman",
    "Fatima",
    "Hamza",
    "Zainab",
    "Bilal",
    "Hina",
]


def seed_database():
    # Everything that touches the database now lives INSIDE the with
    # block, so the automatic commit-on-success / rollback-on-error
    # actually covers the CREATE TABLE, DELETE, and INSERTs below.
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        # parameterized SQL query
        # creates orders table with 200 invented orders
        # (columns: id, customer, product, amount, created_at)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Clear existing data so the script is safe to run twice:
        # not 200+200=400 orders, but 200 orders only.
        cursor.execute("DELETE FROM orders")

        today = date.today()

        for _ in range(200):
            customer = random.choice(CUSTOMERS)
            product = random.choice(PRODUCTS)
            amount = round(random.uniform(5, 200), 2)

            random_days_ago = random.randint(0, 29)
            created_at = today - timedelta(days=random_days_ago)

            cursor.execute(
                """
                INSERT INTO orders (customer, product, amount, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (customer, product, amount, created_at.isoformat()),
            )

        # connection.commit() happens automatically here, since the
        # with block exits successfully with all the work done inside it.

    connection.close()
    print(f"Database seeded successfully with 200 orders at: {DATABASE}")


if __name__ == "__main__":
    seed_database()