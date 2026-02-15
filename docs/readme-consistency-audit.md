# README 一致性审计（修正版）

> 审计范围：仅核对 README 中与 Batch0/Batch1/Batch2 相关叙事是否与当前代码与治理文档一致；不修改 README 正文。
>
> 证据来源：`README.md`、`docs/governance-audit.md`、`docs/governance-fixes.md`、`docs/ranking-source-of-truth.md`、`backend/app/main.py`、`backend/app/models.py`。

## 1) README 当前 Batch0/1/2 摘要

### Batch0
- `README.md` 未出现 Batch0 的显式章节、定义或结论。

### Batch1
- `README.md` 已包含与 Batch1 目标一致的运行路径/目录策略说明：`STATIC_DIR`、`UPLOAD_DIR`、`IMAGE_DIR` 默认值，且相对路径以 `backend/` 为锚点解析。
- `README.md` 也包含后端最小健康检查（`/api/health`）与上传路径一致性约束（`UPLOAD_DIR` 必须解析到 `STATIC_DIR/uploads`）。

### Batch2
- `README.md` 没有显式写出“Batch2 榜单权威路径决策”。
- 现有 README 更多描述“固定 5 维度 + 双榜单”的产品说明，并未明确 `sync_rankings_service()` 为运行时唯一权威路径，也未提示 `calculate_app_score()` 的 deprecated 语义。

## 2) 与当前代码不一致的点

1. **Batch 叙事缺口（README 与治理文档不对齐）**
   - `docs/governance-audit.md`、`docs/governance-fixes.md`、`docs/ranking-source-of-truth.md` 已明确 Batch 1/2 的目标与结论；README 未形成对应批次叙事索引。

2. **榜单机制叙事偏旧，未反映 Batch2 权威路径决策**
   - 治理文档明确：运行时榜单单一真相是 `sync_rankings_service()`；`calculate_app_score()` 仅保留兼容/审计。
   - README API/机制说明未同步该“单一路径”结论，读者仍可能按“旧函数+新服务并存”理解。

3. **数据结构章节未覆盖三层模型核心对象**
   - README 数据结构表未体现 `ranking_configs` 与 `app_ranking_settings` 两张核心表，也未强调 `rankings`/`historical_rankings` 的 `ranking_config_id` 主关联语义。
   - 当前代码模型已采用三层架构实体：`RankingConfig`、`AppRankingSetting`、`ranking_config_id`。

4. **README API 清单与后端实际能力不完全对齐**
   - README 已列旧有核心接口，但未完整覆盖 `ranking-configs`、`apps/{app_id}/ranking-settings`、`app-ranking-settings` 等三层配置接口族。

## 3) 是否存在“双真相”或历史叙事未清理问题

结论：**存在“文档层双真相/历史叙事未清理”问题**。

- **治理文档层面**：Batch2 已明确权威路径与 deprecated 策略。
- **README 层面**：仍以旧叙事为主，未把 Batch2 的“单一路径决策”抬升为对外主叙述。
- **代码可读性层面（补充观察）**：`backend/app/main.py` 存在重复/残片定义痕迹（例如重复函数定义片段），会放大“到底哪条路径是主逻辑”的理解成本；虽不必然改变运行结果，但会加重认知分叉风险。

## 4) 建议调整点（仅建议，不改正文）

1. 在 README 新增“治理批次状态”小节（Batch0/1/2），并链接三份治理文档。
2. 在 README 榜单章节增加一句“运行时唯一权威路径”声明：`sync_rankings_service()`；将 `calculate_app_score()` 标注为兼容/审计用途。
3. 在 README 数据结构补齐三层实体：`ranking_configs`、`app_ranking_settings`，并在 `rankings`/`historical_rankings` 中强调 `ranking_config_id`。
4. 在 README API 补齐三层配置接口组（ranking-configs、app ranking settings）。
5. 代码维护建议：后续单独做一次 `backend/app/main.py` 清理（去重复定义/残片），降低“历史叙事残留”带来的双真相感知。

---

## 审计结论（简版）

- **Batch1（路径与启动稳态）**：README 与治理文档/代码总体一致。
- **Batch2（榜单单一路径治理）**：治理文档与代码已有结论，但 README 主叙事未完成同步，存在文档层双真相。
- **Batch0**：README 无显式内容，建议补最小定义或状态说明，避免读者误判为缺失。
