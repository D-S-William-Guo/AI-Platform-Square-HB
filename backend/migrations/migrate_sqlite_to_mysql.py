#!/usr/bin/env python3
"""
SQLite to MySQL Migration Script
将 SQLite 数据库数据迁移到 MySQL
"""

import sqlite3
import pymysql
from datetime import datetime
from typing import List, Dict, Any

# 配置
SQLITE_DB_PATH = "ai_app_square.db"
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 13306,
    "user": "ai_app_user",
    "password": "ai_app_password",
    "database": "ai_app_square",
    "charset": "utf8mb4"
}


def get_sqlite_data(table_name: str) -> List[Dict[str, Any]]:
    """从 SQLite 读取数据"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def insert_to_mysql(table_name: str, data: List[Dict[str, Any]], column_mapping: Dict[str, str] = None):
    """插入数据到 MySQL"""
    if not data:
        print(f"表 {table_name} 没有数据需要迁移")
        return

    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # 获取列名
    columns = list(data[0].keys())
    if column_mapping:
        columns = [column_mapping.get(col, col) for col in columns]

    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join([f"`{col}`" for col in columns])

    sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"

    try:
        for row in data:
            values = list(row.values())
            # 处理布尔值
            values = [
                int(v) if isinstance(v, bool) else v
                for v in values
            ]
            cursor.execute(sql, values)

        conn.commit()
        print(f"表 {table_name} 迁移成功，共 {len(data)} 条记录")
    except Exception as e:
        conn.rollback()
        print(f"表 {table_name} 迁移失败: {e}")
    finally:
        cursor.close()
        conn.close()


def migrate_apps():
    """迁移 apps 表"""
    print("\n迁移 apps 表...")
    data = get_sqlite_data("apps")
    # 处理日期格式
    for row in data:
        if 'release_date' in row and row['release_date']:
            # SQLite 返回的是字符串，需要保持格式
            pass
    insert_to_mysql("apps", data)


def migrate_rankings():
    """迁移 rankings 表"""
    print("\n迁移 rankings 表...")
    data = get_sqlite_data("rankings")
    insert_to_mysql("rankings", data)


def migrate_submissions():
    """迁移 submissions 表"""
    print("\n迁移 submissions 表...")
    data = get_sqlite_data("submissions")
    insert_to_mysql("submissions", data)


def migrate_submission_images():
    """迁移 submission_images 表"""
    print("\n迁移 submission_images 表...")
    data = get_sqlite_data("submission_images")
    insert_to_mysql("submission_images", data)


def migrate_ranking_dimensions():
    """迁移 ranking_dimensions 表"""
    print("\n迁移 ranking_dimensions 表...")
    data = get_sqlite_data("ranking_dimensions")
    insert_to_mysql("ranking_dimensions", data)


def migrate_ranking_logs():
    """迁移 ranking_logs 表"""
    print("\n迁移 ranking_logs 表...")
    data = get_sqlite_data("ranking_logs")
    insert_to_mysql("ranking_logs", data)


def migrate_app_dimension_scores():
    """迁移 app_dimension_scores 表"""
    print("\n迁移 app_dimension_scores 表...")
    data = get_sqlite_data("app_dimension_scores")
    insert_to_mysql("app_dimension_scores", data)


def migrate_historical_rankings():
    """迁移 historical_rankings 表"""
    print("\n迁移 historical_rankings 表...")
    data = get_sqlite_data("historical_rankings")
    insert_to_mysql("historical_rankings", data)


def verify_migration():
    """验证迁移结果"""
    print("\n验证迁移结果...")

    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    tables = ["apps", "rankings", "submissions", "submission_images", 
              "ranking_dimensions", "ranking_logs", "app_dimension_scores", "historical_rankings"]
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} 条记录")
        except Exception as e:
            print(f"  {table}: 查询失败 - {e}")

    cursor.close()
    conn.close()


def main():
    print("=" * 60)
    print("SQLite 到 MySQL 数据迁移")
    print("=" * 60)
    print(f"源数据库: {SQLITE_DB_PATH}")
    print(f"目标数据库: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}")
    print("=" * 60)

    try:
        migrate_apps()
        migrate_rankings()
        migrate_submissions()
        migrate_submission_images()
        migrate_ranking_dimensions()
        migrate_ranking_logs()
        migrate_app_dimension_scores()
        migrate_historical_rankings()

        print("\n" + "=" * 60)
        verify_migration()
        print("=" * 60)
        print("迁移完成！")

    except Exception as e:
        print(f"\n迁移过程中出错: {e}")
        raise


if __name__ == "__main__":
    main()
