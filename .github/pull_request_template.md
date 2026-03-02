## What
- [ ] 简述本 PR 做了什么（1-3 条）

## Why
- [ ] 触发原因/背景（需求、缺陷、治理、重构等）

## Changes
- [ ] 关键变更点（面向审阅者，列文件/模块/行为变化）

## How to verify
- [ ] 已跑 doctor（Linux: `bash backend/scripts/dev/doctor.sh` / Windows: `powershell -ExecutionPolicy Bypass -File backend\\scripts\\dev\\doctor.ps1`）
- [ ] backend tests：`python -m pytest -q tests`
- [ ] frontend build：`npm run build`
- [ ] 若涉及 migrations：已说明新增/变更 migration 文件 + 验证方式
- [ ] docs/README 是否需要同步（如有则已更新）

## Definition of Done (DoD)
- [ ] PR 描述已完整（What/Why/Changes/Verify）
- [ ] 已自测：核心路径可用
- [ ] 不引入无关重构/大范围格式化
- [ ] 与 main 同步，无冲突（必要时 rebase）
- [ ] CI 全绿（Required checks 全通过）
