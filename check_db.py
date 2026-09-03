import sqlite3

connection = sqlite3.connect("report.db")

cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM orders")

count = cursor.fetchone()[0]

print(f"Total orders: {count}")

connection.close()