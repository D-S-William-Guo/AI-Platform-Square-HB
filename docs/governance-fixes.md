# Governance Fixes Log

## Batch 1 - P0 运行/启动硬风险修复

### 目标
- 避免因缺失 `static/`、上传目录、图片目录导致后端启动失败。
- 保持现有 `/static/...` URL 与上传 API 行为不变。
- 提供可复现的最小启动验证。

### 变更说明
1. **静态目录策略**
   - 采用“启动时自动创建目录 + 保持 `/static` 挂载不变”的方案。
   - 理由：
     - 不改已有静态 URL 行为；
     - 比“仅目录存在时挂载”更稳，不会因目录缺失导致启动失败；
     - 对现有前端与上传返回链接完全兼容。
2. **上传/图片目录统一配置**
   - 新增配置项：`STATIC_DIR`、`UPLOAD_DIR`、`IMAGE_DIR`（优先级为 env 覆盖默认值）。
   - 默认值：`static`、`static/uploads`、`static/images`。
   - 在 `startup` 中统一 `mkdir -p`。
3. **最小验证链路补齐**
   - README 增加后端最小健康检查步骤（启动 + `curl /api/health`）。

### 验证方式
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

新开终端：
```bash
curl -sS http://127.0.0.1:8000/api/health
```
期望返回：`{"status":"ok"}`。

### 回滚方式
- 直接回滚 commit `fix(p0): harden static/uploads directories`。
- 若只需临时回退路径配置，可恢复 `backend/app/main.py` 中原始 `Path("static/uploads")` 与 `StaticFiles(directory="static")`。

## Batch 1 补充 - cwd/路径一致性验证（版本二主线）

### 背景
- 根据评审意见，采用“版本二”作为主线：运行时目录使用统一的锚点解析，避免因不同启动目录（cwd）导致 `static/uploads/images` 落点漂移。

### 调整
- 新增 `resolve_runtime_path()`，将 `STATIC_DIR`、`UPLOAD_DIR`、`IMAGE_DIR` 的相对路径固定解析到 `backend/` 目录。
- 绝对路径配置保持原样，不做重写。

### 验证命令
```bash
cd /workspace/AI-Platform-Square-HB
python - <<'PY'
from backend.app.main import STATIC_DIR, UPLOAD_DIR, IMAGE_DIR
print(STATIC_DIR)
print(UPLOAD_DIR)
print(IMAGE_DIR)
PY

cd /workspace/AI-Platform-Square-HB/backend
python - <<'PY'
from app.main import STATIC_DIR, UPLOAD_DIR, IMAGE_DIR
print(STATIC_DIR)
print(UPLOAD_DIR)
print(IMAGE_DIR)
PY
```

期望两次输出一致，且均落在 `<repo>/backend/static`、`<repo>/backend/static/uploads`、`<repo>/backend/static/images`。

## Batch 2 - P1 榜单“双真相”治理（不改业务结果）

### 目标
- 明确榜单计算的权威路径，避免配置已改但结果来源不清。
- 保留兼容接口，不变更现有 API 路径和响应结构。

### 变更说明
1. **权威路径明确**
   - 以 `sync_rankings_service()`（三层榜单配置 + AppRankingSetting）作为默认且唯一权威计算路径。
   - 抽取 `calculate_three_layer_score()` 作为纯计算函数，供权威路径复用并便于回归测试。
2. **旧逻辑降级为审计用途**
   - `calculate_app_score()` 增加 Deprecated 标识与日志告警：保留函数仅用于审计/回顾，不作为生产榜单计算主路径。
3. **最小一致性回归锚点**
   - 新增测试 `test_three_layer_score_is_stable_for_same_input`，验证相同输入输出稳定。

### 验证命令
```bash
cd /workspace/AI-Platform-Square-HB/backend
PYTHONPATH=. pytest -q tests/test_ranking_consistency.py tests/test_api.py::test_health
```

### 回滚方式
- 回滚 commit `chore(ranking): clarify single source of truth (no behavior change)`。
