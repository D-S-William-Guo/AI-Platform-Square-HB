"""
数据完整性测试脚本

用于验证数据库中的数据一致性和完整性
"""

import sqlite3
import sys
from datetime import datetime
from typing import List, Tuple


class DataIntegrityTest:
    """数据完整性测试类"""
    
    def __init__(self, db_path: str = 'ai_app_square.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("=" * 80)
        print("数据完整性测试开始")
        print("=" * 80)
        print(f"数据库: {self.db_path}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        tests = [
            self.test_apps_table,
            self.test_submissions_table,
            self.test_rankings_table,
            self.test_historical_rankings_table,
            self.test_ranking_dimensions_table,
            self.test_app_dimension_scores_table,
            self.test_data_relationships,
            self.test_data_consistency
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.errors.append(f"测试 {test.__name__} 执行失败: {str(e)}")
        
        self.print_results()
        return len(self.errors) == 0
    
    def test_apps_table(self):
        """测试 apps 表数据完整性"""
        print("【测试】apps 表数据完整性...")
        
        # 检查必填字段
        self.cursor.execute("""
            SELECT id, name, org, section, category, status 
            FROM apps 
            WHERE name IS NULL OR name = ''
               OR org IS NULL OR org = ''
               OR section IS NULL OR section = ''
               OR category IS NULL OR category = ''
               OR status IS NULL OR status = ''
        """)
        invalid_apps = self.cursor.fetchall()
        if invalid_apps:
            self.errors.append(f"apps 表有 {len(invalid_apps)} 条记录缺少必填字段")
        
        # 检查 section 值有效性
        self.cursor.execute("""
            SELECT id, name, section FROM apps 
            WHERE section NOT IN ('group', 'province')
        """)
        invalid_section = self.cursor.fetchall()
        if invalid_section:
            self.errors.append(f"apps 表有 {len(invalid_section)} 条记录的 section 值无效")
        
        # 统计
        self.cursor.execute("SELECT COUNT(*) FROM apps")
        total_apps = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM apps WHERE section='group'")
        group_apps = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM apps WHERE section='province'")
        province_apps = self.cursor.fetchone()[0]
        
        print(f"  ✓ 总应用数: {total_apps} (集团: {group_apps}, 省内: {province_apps})")
    
    def test_submissions_table(self):
        """测试 submissions 表数据完整性"""
        print("【测试】submissions 表数据完整性...")
        
        # 检查状态值有效性
        self.cursor.execute("""
            SELECT id, app_name, status FROM submissions 
            WHERE status NOT IN ('pending', 'approved', 'rejected')
        """)
        invalid_status = self.cursor.fetchall()
        if invalid_status:
            self.errors.append(f"submissions 表有 {len(invalid_status)} 条记录的 status 值无效")
        
        # 统计
        self.cursor.execute("SELECT COUNT(*) FROM submissions")
        total = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'")
        pending = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='approved'")
        approved = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='rejected'")
        rejected = self.cursor.fetchone()[0]
        
        print(f"  ✓ 总申报数: {total} (待审核: {pending}, 已通过: {approved}, 已拒绝: {rejected})")
    
    def test_rankings_table(self):
        """测试 rankings 表数据完整性"""
        print("【测试】rankings 表数据完整性...")
        
        # 检查排名是否连续
        self.cursor.execute("""
            SELECT position FROM rankings 
            WHERE ranking_type='excellent'
            ORDER BY position
        """)
        positions = [row[0] for row in self.cursor.fetchall()]
        
        if positions:
            expected_positions = list(range(1, len(positions) + 1))
            if positions != expected_positions:
                self.warnings.append("rankings 表排名位置不连续")
        
        # 检查应用是否存在
        self.cursor.execute("""
            SELECT r.id, r.app_id FROM rankings r
            LEFT JOIN apps a ON r.app_id = a.id
            WHERE a.id IS NULL
        """)
        orphaned = self.cursor.fetchall()
        if orphaned:
            self.errors.append(f"rankings 表有 {len(orphaned)} 条记录关联的应用不存在")
        
        # 统计
        self.cursor.execute("SELECT COUNT(*) FROM rankings")
        total = self.cursor.fetchone()[0]
        print(f"  ✓ 当前榜单应用数: {total}")
    
    def test_historical_rankings_table(self):
        """测试 historical_rankings 表数据完整性"""
        print("【测试】historical_rankings 表数据完整性...")
        
        # 检查日期分布
        self.cursor.execute("""
            SELECT period_date, COUNT(*) as count 
            FROM historical_rankings 
            GROUP BY period_date 
            ORDER BY period_date DESC
        """)
        dates = self.cursor.fetchall()
        
        print(f"  ✓ 历史榜单日期数: {len(dates)}")
        for date_row in dates[:5]:  # 只显示最近5个日期
            print(f"    - {date_row[0]}: {date_row[1]} 条记录")
    
    def test_ranking_dimensions_table(self):
        """测试 ranking_dimensions 表数据完整性"""
        print("【测试】ranking_dimensions 表数据完整性...")
        
        # 检查权重范围
        self.cursor.execute("""
            SELECT id, name, weight FROM ranking_dimensions 
            WHERE weight < 0.1 OR weight > 10.0
        """)
        invalid_weights = self.cursor.fetchall()
        if invalid_weights:
            self.warnings.append(f"ranking_dimensions 表有 {len(invalid_weights)} 个维度的权重超出范围")
        
        # 统计
        self.cursor.execute("SELECT COUNT(*) FROM ranking_dimensions")
        total = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM ranking_dimensions WHERE is_active=1")
        active = self.cursor.fetchone()[0]
        
        print(f"  ✓ 总维度数: {total} (启用: {active}, 禁用: {total - active})")
        
        # 显示维度详情
        self.cursor.execute("""
            SELECT name, weight, is_active FROM ranking_dimensions 
            ORDER BY weight DESC
        """)
        for row in self.cursor.fetchall():
            status = "启用" if row[2] else "禁用"
            print(f"    - {row[0]}: 权重 {row[1]} ({status})")
    
    def test_app_dimension_scores_table(self):
        """测试 app_dimension_scores 表数据完整性"""
        print("【测试】app_dimension_scores 表数据完整性...")
        
        # 检查评分范围
        self.cursor.execute("""
            SELECT id, app_id, dimension_id, score 
            FROM app_dimension_scores 
            WHERE score < 0 OR score > 100
        """)
        invalid_scores = self.cursor.fetchall()
        if invalid_scores:
            self.errors.append(f"app_dimension_scores 表有 {len(invalid_scores)} 条记录的评分超出范围(0-100)")
        
        # 统计
        self.cursor.execute("SELECT COUNT(*) FROM app_dimension_scores")
        total = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(DISTINCT period_date) FROM app_dimension_scores")
        date_count = self.cursor.fetchone()[0]
        
        print(f"  ✓ 总评分记录数: {total} (涉及 {date_count} 个日期)")
    
    def test_data_relationships(self):
        """测试数据关系完整性"""
        print("【测试】数据关系完整性...")
        
        # 检查已通过申报是否都有对应应用
        self.cursor.execute("""
            SELECT s.id, s.app_name 
            FROM submissions s
            LEFT JOIN apps a ON s.app_name = a.name
            WHERE s.status = 'approved' AND a.id IS NULL
        """)
        unmatched = self.cursor.fetchall()
        if unmatched:
            self.warnings.append(f"有 {len(unmatched)} 个已通过申报没有对应应用")
            for row in unmatched:
                print(f"    ⚠ 申报 '{row[1]}' (ID:{row[0]}) 无对应应用")
        else:
            print("  ✓ 所有已通过申报都有对应应用")
        
        # 检查省内应用是否都有申报记录
        self.cursor.execute("""
            SELECT a.id, a.name 
            FROM apps a
            LEFT JOIN submissions s ON a.name = s.app_name
            WHERE a.section = 'province' AND s.id IS NULL
        """)
        no_submission = self.cursor.fetchall()
        if no_submission:
            self.warnings.append(f"有 {len(no_submission)} 个省内应用没有申报记录")
        else:
            print("  ✓ 所有省内应用都有申报记录")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        print("【测试】数据一致性...")
        
        # 检查榜单应用是否都在 apps 表中
        self.cursor.execute("""
            SELECT DISTINCT r.app_id 
            FROM rankings r
            WHERE r.app_id NOT IN (SELECT id FROM apps)
        """)
        invalid_apps = self.cursor.fetchall()
        if invalid_apps:
            self.errors.append(f"rankings 表有 {len(invalid_apps)} 个 app_id 在 apps 表中不存在")
        else:
            print("  ✓ 榜单应用数据一致")
        
        # 检查历史榜单日期是否有效
        self.cursor.execute("""
            SELECT period_date FROM historical_rankings 
            WHERE period_date > DATE('now')
        """)
        future_dates = self.cursor.fetchall()
        if future_dates:
            self.warnings.append(f"historical_rankings 表有 {len(future_dates)} 条未来日期的记录")
    
    def print_results(self):
        """打印测试结果"""
        print()
        print("=" * 80)
        print("测试结果汇总")
        print("=" * 80)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 所有测试通过，数据完整性良好！")
        elif not self.errors:
            print("\n✅ 数据完整性基本良好（仅有警告）")
        else:
            print("\n❌ 数据完整性存在问题，需要修复")
        
        print()
        print("=" * 80)
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def main():
    """主函数"""
    test = DataIntegrityTest()
    try:
        success = test.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        test.close()


if __name__ == '__main__':
    main()
