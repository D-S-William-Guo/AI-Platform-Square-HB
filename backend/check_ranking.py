import sqlite3
from datetime import datetime

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print("检查 rankings 表的 declared_at 字段:")
cursor.execute("SELECT id, declared_at FROM rankings LIMIT 5")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, declared_at: {row[1]}, type: {type(row[1])}")

print("\n检查 historical_rankings 表的 period_date 字段:")
cursor.execute("SELECT id, period_date FROM historical_rankings LIMIT 5")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, period_date: {row[1]}, type: {type(row[1])}")

conn.close()
