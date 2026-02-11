import sqlite3
from datetime import datetime

conn = sqlite3.connect('ai_app_square.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("数据完整性验证报告")
print("=" * 80)

# 1. 验证申报数据
print("\n【1. 申报数据验证】")
cursor.execute("SELECT * FROM submissions ORDER BY id")
submissions = cursor.fetchall()
print(f"总申报数: {len(submissions)}")

approved_count = sum(1 for s in submissions if s['status'] == 'approved')
pending_count = sum(1 for s in submissions if s['status'] == 'pending')
print(f"  - 已通过: {approved_count}")
print(f"  - 待审核: {pending_count}")

print("\n申报详情:")
for s in submissions:
    print(f"  ID:{s['id']} | {s['app_name'][:20]:<20} | 状态:{s['status']:<10} | 时间:{s['created_at']}")

# 2. 验证省内应用数据
print("\n【2. 省内应用验证】")
cursor.execute("SELECT * FROM apps WHERE section='province' ORDER BY id")
province_apps = cursor.fetchall()
print(f"省内应用总数: {len(province_apps)}")

print("\n省内应用详情:")
for app in province_apps:
    print(f"  ID:{app['id']} | {app['name'][:20]:<20} | 单位:{app['org']:<15} | 调用量:{app['monthly_calls']}k")

# 3. 验证申报与应用的关联关系
print("\n【3. 申报-应用关联验证】")
cursor.execute("""
    SELECT s.id as submission_id, s.app_name as submission_name, 
           a.id as app_id, a.name as app_name, s.status
    FROM submissions s
    LEFT JOIN apps a ON s.app_name = a.name
    WHERE s.status = 'approved'
    ORDER BY s.id
""")
relations = cursor.fetchall()

print("\n已通过申报对应的应用:")
for r in relations:
    if r['app_id']:
        print(f"  ✓ 申报ID:{r['submission_id']} -> 应用ID:{r['app_id']} | {r['submission_name']}")
    else:
        print(f"  ✗ 申报ID:{r['submission_id']} 无对应应用 | {r['submission_name']}")

# 4. 验证排行榜数据
print("\n【4. 排行榜数据验证】")
cursor.execute("SELECT * FROM rankings ORDER BY position")
rankings = cursor.fetchall()
print(f"当前榜单应用数: {len(rankings)}")

for r in rankings:
    cursor.execute("SELECT name, section FROM apps WHERE id=?", (r['app_id'],))
    app = cursor.fetchone()
    if app:
        print(f"  排名#{r['position']} | {app['name'][:20]:<20} | 区域:{app['section']:<10} | 得分:{r['score']}")

# 5. 验证历史榜单数据
print("\n【5. 历史榜单数据验证】")
cursor.execute("SELECT DISTINCT period_date FROM historical_rankings ORDER BY period_date DESC")
dates = cursor.fetchall()
print(f"历史榜单日期数: {len(dates)}")
for d in dates:
    cursor.execute("SELECT COUNT(*) FROM historical_rankings WHERE period_date=?", (d['period_date'],))
    count = cursor.fetchone()[0]
    print(f"  日期 {d['period_date']}: {count} 条记录")

# 6. 验证维度评分数据
print("\n【6. 维度评分数据验证】")
cursor.execute("SELECT * FROM ranking_dimensions WHERE is_active=1")
dimensions = cursor.fetchall()
print(f"活跃维度数: {len(dimensions)}")
for dim in dimensions:
    cursor.execute("SELECT COUNT(*) FROM app_dimension_scores WHERE dimension_id=?", (dim['id'],))
    count = cursor.fetchone()[0]
    print(f"  维度 '{dim['name']}': {count} 个应用评分")

print("\n" + "=" * 80)
print("验证完成")
print("=" * 80)

conn.close()
