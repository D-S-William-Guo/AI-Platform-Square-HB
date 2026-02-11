import sqlite3
conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()
print('=== 当前排行榜维度 ===')
cursor.execute('SELECT id, name, description, calculation_method, weight, is_active FROM ranking_dimensions ORDER BY id')
for row in cursor.fetchall():
    status = '启用' if row[5] else '禁用'
    print(f"ID: {row[0]}")
    print(f"  名称: {row[1]}")
    print(f"  描述: {row[2]}")
    print(f"  计算方法: {row[3]}")
    print(f"  权重: {row[4]}")
    print(f"  状态: {status}")
    print()
conn.close()
