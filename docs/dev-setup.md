# 开发环境快速启动（Backend）

目标：不依赖 `PYTHONPATH`，统一使用 `pip install -e backend`（editable install），保证 Linux / Windows / Codex 一致。

---

## Linux（云电脑/服务器）

一键初始化 venv（默认落到 BigData）并跑测试：
```bash
bash backend/scripts/dev/bootstrap_venv.sh
```

默认路径：

- venv：`/home/ctyun/BigData/.venvs/ai-platform-square-hb`
- pip cache：`/home/ctyun/BigData/.pip-cache`

自定义路径（可选）：
```bash
VENV_DIR=/path/to/venv PIP_CACHE_DIR=/path/to/pip-cache bash backend/scripts/dev/bootstrap_venv.sh
```

环境自检（建议每次改依赖/换机器后跑一次）：
```bash
cd backend
python -m pip install -e .
python -c "import app; import app.main; print('editable ok')"
pytest -q tests
```

---

## Windows（PowerShell）

建议：在 `backend` 目录创建项目 venv，并做 editable install。
```powershell
cd <your-repo>\backend
py -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -e .
.\.venv\Scripts\pytest -q tests
```

---

## Codex（网页版/远程环境）

原则同上：进入 `backend`，安装依赖并 editable install，再跑 tests。
```bash
cd backend
python -m pip install -r requirements.txt
python -m pip install -e .
pytest -q tests
```
