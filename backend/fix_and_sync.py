import sqlite3
from datetime import datetime

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print("=== 修复趋势榜数据 ===\n")

# 1. 先检查当前趋势榜数据
cursor.execute("""
    SELECT id, position, app_id, score
    FROM rankings
    WHERE ranking_type = 'trend'
    ORDER BY score DESC
""")
rows = cursor.fetchall()
print(f"修复前趋势榜数据 ({len(rows)}条):")
for row in rows:
    print(f"  ID:{row[0]} 位置:{row[1]} 应用ID:{row[2]} 分数:{row[3]}")

# 2. 按分数重新排序并更新位置
print("\n正在修复排名位置...")
cursor.execute("""
    SELECT id, score
    FROM rankings
    WHERE ranking_type = 'trend'
    ORDER BY score DESC
""")
rows = cursor.fetchall()

for index, row in enumerate(rows, start=1):
    cursor.execute("""
        UPDATE rankings
        SET position = ?
        WHERE id = ?
    """, (index, row[0]))
    print(f"  ID:{row[0]} -> 位置{index}")

conn.commit()

# 3. 同步到历史榜单
print("\n正在同步到历史榜单...")
today = datetime.now().date()

# 删除今天已有的趋势榜历史数据
cursor.execute("""
    DELETE FROM historical_rankings
    WHERE ranking_type = 'trend' AND period_date = ?
""", (today,))

# 插入新的历史数据
cursor.execute("""
    SELECT r.position, r.app_id, a.name, a.org, r.tag, r.score, r.metric_type, r.value_dimension, r.usage_30d
    FROM rankings r
    JOIN apps a ON r.app_id = a.id
    WHERE r.ranking_type = 'trend'
    ORDER BY r.position
""")
rows = cursor.fetchall()

for row in rows:
    cursor.execute("""
        INSERT INTO historical_rankings
        (ranking_type, period_date, position, app_id, app_name, app_org, tag, score, metric_type, value_dimension, usage_30d, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, ('trend', today, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))
    print(f"  已插入: {row[2]} 排名{row[0]}")

conn.commit()

# 4. 验证修复结果
print("\n=== 修复后验证 ===")
cursor.execute("""
    SELECT id, position, app_id, score
    FROM rankings
    WHERE ranking_type = 'trend'
    ORDER BY position
""")
rows = cursor.fetchall()
print(f"\nrankings表趋势榜 ({len(rows)}条):")
for row in rows:
    print(f"  排名{row[1]}: {row[3]}分 (应用ID:{row[2]})")

cursor.execute("""
    SELECT period_date, position, app_name, score
    FROM historical_rankings
    WHERE ranking_type = 'trend'
    ORDER BY period_date DESC, position
""")
rows = cursor.fetchall()
print(f"\nhistorical_rankings表趋势榜 ({len(rows)}条):")
for row in rows:
    print(f"  {row[0]} 排名{row[1]}: {row[3]}分 - {row[2]}")

conn.close()
print("\n修复完成!")
