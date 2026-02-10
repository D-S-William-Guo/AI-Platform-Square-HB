import sqlite3

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print("=== 检查趋势榜数据 ===\n")

print("1. 当前rankings表中的趋势榜数据:")
cursor.execute("""
    SELECT r.id, r.position, r.app_id, a.name, r.score, r.tag 
    FROM rankings r
    JOIN apps a ON r.app_id = a.id
    WHERE r.ranking_type = 'trend'
    ORDER BY r.position
""")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  排名{row[1]}: {row[4]}分 - {row[3]} (ID:{row[2]})")
else:
    print("  暂无趋势榜数据")

print("\n2. 历史榜单中的趋势榜数据:")
cursor.execute("""
    SELECT period_date, COUNT(*) as count 
    FROM historical_rankings 
    WHERE ranking_type = 'trend'
    GROUP BY period_date
    ORDER BY period_date DESC
""")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  {row[0]}: {row[1]} 条记录")
        
        # 显示该日期的前3名
        cursor.execute("""
            SELECT position, app_name, score 
            FROM historical_rankings 
            WHERE ranking_type = 'trend' AND period_date = ?
            ORDER BY position
            LIMIT 3
        """, (row[0],))
        top3 = cursor.fetchall()
        for r in top3:
            print(f"    #{r[0]}: {r[2]}分 - {r[1]}")
else:
    print("  暂无历史趋势榜数据")

print("\n3. 省内应用的排行配置:")
cursor.execute("""
    SELECT id, name, ranking_enabled, ranking_weight, ranking_tags
    FROM apps
    WHERE section = 'province'
    ORDER BY id
""")
rows = cursor.fetchall()
for row in rows:
    status = "参与" if row[2] else "不参与"
    print(f"  {row[1]}: {status}, 权重{row[3]}, 标签'{row[4]}'")

conn.close()
