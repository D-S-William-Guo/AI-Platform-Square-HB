import sqlite3

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print('=== 申报数据状态 ===')
cursor.execute("SELECT id, app_name, status, created_at FROM submissions ORDER BY id")
for row in cursor.fetchall():
    print(f'ID: {row[0]}, 名称: {row[1]}, 状态: {row[2]}, 时间: {row[3]}')

print('\n=== 省内应用数据 ===')
cursor.execute("SELECT id, name, section, org FROM apps WHERE section='province' ORDER BY id")
for row in cursor.fetchall():
    print(f'ID: {row[0]}, 名称: {row[1]}, 区域: {row[2]}, 单位: {row[3]}')

conn.close()
