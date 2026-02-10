import sqlite3

conn = sqlite3.connect('ai_app_square.db')
cursor = conn.cursor()

print("修复排行榜数据重复问题...")

# 1. 清除重复的rankings数据
cursor.execute("DELETE FROM rankings")

# 2. 重新插入正确的省内应用排行数据（只插入省内应用）
from datetime import datetime
current_time = datetime.now().isoformat()

cursor.execute("""
    INSERT INTO rankings (ranking_type, position, app_id, tag, score, metric_type, value_dimension, usage_30d, declared_at, updated_at)
    SELECT 
        'excellent',
        ROW_NUMBER() OVER (ORDER BY a.monthly_calls DESC, a.id DESC),
        a.id,
        CASE 
            WHEN a.monthly_calls > 20 THEN '推荐'
            WHEN a.monthly_calls > 10 THEN '历史优秀'
            ELSE '新晋'
        END,
        CAST(a.monthly_calls * 10 + 100 AS INTEGER),
        'composite',
        'efficiency_gain',
        CAST(a.monthly_calls * 1000 AS INTEGER),
        ?,
        ?
    FROM apps a
    WHERE a.section = 'province'
    ORDER BY a.monthly_calls DESC, a.id DESC
""", (current_time, current_time))

# 3. 清除历史榜单数据并重新插入
cursor.execute("DELETE FROM historical_rankings")

# 4. 重新插入历史榜单数据（只插入省内应用）
cursor.execute("""
    INSERT INTO historical_rankings (ranking_type, period_date, position, app_id, app_name, app_org, tag, score, metric_type, value_dimension, usage_30d, created_at)
    SELECT 
        'excellent',
        DATE('now'),
        ROW_NUMBER() OVER (ORDER BY a.monthly_calls DESC, a.id DESC),
        a.id,
        a.name,
        a.org,
        CASE 
            WHEN a.monthly_calls > 20 THEN '推荐'
            WHEN a.monthly_calls > 10 THEN '历史优秀'
            ELSE '新晋'
        END,
        CAST(a.monthly_calls * 10 + 100 AS INTEGER),
        'composite',
        'efficiency_gain',
        CAST(a.monthly_calls * 1000 AS INTEGER),
        ?
    FROM apps a
    WHERE a.section = 'province'
    ORDER BY a.monthly_calls DESC, a.id DESC
""", (current_time,))

conn.commit()

# 验证修复结果
print("\n修复后的排行榜数据:")
cursor.execute("""
    SELECT r.position, a.name, a.section, r.score 
    FROM rankings r 
    JOIN apps a ON r.app_id = a.id 
    ORDER BY r.position
""")
for row in cursor.fetchall():
    print(f"  排名#{row[0]} | {row[1]} | 区域:{row[2]} | 得分:{row[3]}")

print("\n修复后的历史榜单数据:")
cursor.execute("SELECT DISTINCT period_date, COUNT(*) FROM historical_rankings GROUP BY period_date")
for row in cursor.fetchall():
    print(f"  日期 {row[0]}: {row[1]} 条记录")

conn.close()
print("\n修复完成！")
