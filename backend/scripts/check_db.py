import sqlite3

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

# 检查所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# 检查submissions表结构
if any('submissions' in t for t in tables):
    cursor.execute('PRAGMA table_info(submissions)')
    print("\nSubmissions table:")
    for row in cursor.fetchall():
        print(row)
else:
    print("\nNo submissions table found")

conn.close()
