import sqlite3
from datetime import datetime

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print("=== 调试同步问题 ===\n")

# 检查rankings表中的趋势榜数据
cursor.execute("""
    SELECT id, position, app_id, score, tag, metric_type
    FROM rankings
    WHERE ranking_type = 'trend'
    ORDER BY score DESC
""")
rows = cursor.fetchall()
print(f"rankings表中的趋势榜数据 ({len(rows)}条):")
for row in rows:
    print(f"  ID:{row[0]} 位置:{row[1]} 应用ID:{row[2]} 分数:{row[3]} 标签:{row[4]} 指标:{row[5]}")

# 检查historical_rankings表中的趋势榜数据
cursor.execute("""
    SELECT id, period_date, position, app_id, app_name, score
    FROM historical_rankings
    WHERE ranking_type = 'trend'
    ORDER BY period_date DESC, position
""")
rows = cursor.fetchall()
print(f"\nhistorical_rankings表中的趋势榜数据 ({len(rows)}条):")
for row in rows:
    print(f"  {row[1]} 排名{row[2]}: {row[5]}分 - {row[4]} (ID:{row[3]})")

# 检查应用数据
cursor.execute("""
    SELECT id, name, section, monthly_calls, ranking_enabled
    FROM apps
    WHERE section = 'province'
""")
rows = cursor.fetchall()
print(f"\n省内应用 ({len(rows)}个):")
for row in rows:
    print(f"  {row[1]}: 调用量{row[3]}, 参与排行:{bool(row[4])}")

conn.close()
