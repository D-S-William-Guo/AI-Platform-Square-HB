from pathlib import Path

from app.config import BACKEND_DIR, resolve_runtime_path


def test_runtime_relative_paths_are_anchored_to_backend_dir():
    assert resolve_runtime_path("static") == (BACKEND_DIR / "static").resolve()
    assert resolve_runtime_path("static/uploads") == (BACKEND_DIR / "static/uploads").resolve()
    assert resolve_runtime_path("static/images") == (BACKEND_DIR / "static/images").resolve()


def test_runtime_absolute_path_is_preserved():
    absolute = Path("/tmp/ai-platform-square-static")
    assert resolve_runtime_path(str(absolute)) == absolute
