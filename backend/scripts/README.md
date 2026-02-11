# Scripts 目录

此目录包含开发调试用的脚本工具，用于数据检查、修复和验证。

## 文件说明

### 数据库初始化
- `init_db.py` - 初始化数据库表结构

### 数据检查脚本
- `check_data.py` - 检查申报和应用数据
- `check_db.py` - 检查数据库表结构
- `check_ranking.py` - 检查排行榜日期字段
- `check_dimensions.py` - 检查排行榜维度配置
- `check_trend_ranking.py` - 检查趋势榜数据
- `verify_data.py` - 数据完整性验证报告

### 数据修复脚本
- `fix_rankings.py` - 修复排行榜数据重复问题
- `fix_declared_at.py` - 修复 declared_at 日期格式
- `fix_and_sync.py` - 修复趋势榜并同步到历史榜单

### 调试测试脚本
- `debug_sync.py` - 调试同步问题
- `test_sync.py` - 测试同步 API

## 使用方式

```bash
cd backend/scripts
python check_data.py
```

**注意**: 这些脚本仅用于开发和调试，生产环境请勿使用。
