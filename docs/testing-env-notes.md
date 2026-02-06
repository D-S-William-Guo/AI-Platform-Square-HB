# 依赖安装与测试环境说明

## 当前现象

- `pip install -r backend/requirements.txt` 通过代理拉取 PyPI 时返回 403。
- 取消代理后，外网 `pypi.org` 网络不可达（`Network is unreachable`）。
- `npm install` 访问 `registry.npmjs.org` 也返回 403。

## 结论

该环境属于“必须走代理，但代理策略不放行 PyPI/npm registry”的组合限制，
不是项目代码本身问题。

## 建议的完善方案（可执行优先级）

1. **公司内网镜像源（推荐）**
   - Python: 配置内部 PyPI mirror（如 Artifactory / Nexus）
   - Node: 配置内部 npm mirror
2. **CI 预装依赖缓存**
   - 在可联网构建机生成 wheel / npm cache
   - 当前环境仅做离线安装
3. **容器化统一构建**
   - 使用公司允许的基础镜像，镜像内预置依赖

## 当前已完成的“离线可做验证”

- Python 语法编译检查：`python -m py_compile backend/app/*.py backend/tests/test_api.py`
- 代码结构与接口定义检查：通过文件级审阅确认

