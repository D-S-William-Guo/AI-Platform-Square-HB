import sqlite3
from datetime import datetime

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print("修复 rankings 表的 declared_at 字段...")

# 获取所有记录
cursor.execute("SELECT id, declared_at FROM rankings")
rows = cursor.fetchall()

for row in rows:
    id_val = row[0]
    declared_at = row[1]
    
    # 如果包含时间部分，提取日期部分
    if isinstance(declared_at, str) and 'T' in declared_at:
        date_part = declared_at.split('T')[0]
        cursor.execute(
            "UPDATE rankings SET declared_at = ? WHERE id = ?",
            (date_part, id_val)
        )
        print(f"  修复 ID {id_val}: {declared_at} -> {date_part}")

conn.commit()

print("\n修复完成！")

# 验证修复结果
print("\n验证修复后的数据:")
cursor.execute("SELECT id, declared_at FROM rankings LIMIT 5")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, declared_at: {row[1]}")

conn.close()
