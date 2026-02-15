from pathlib import Path

import pytest

from app.config import BACKEND_DIR, resolve_runtime_path
from app.main import validate_static_upload_path_consistency


def test_runtime_relative_paths_are_anchored_to_backend_dir():
    assert resolve_runtime_path("static") == (BACKEND_DIR / "static").resolve()
    assert resolve_runtime_path("static/uploads") == (BACKEND_DIR / "static/uploads").resolve()
    assert resolve_runtime_path("static/images") == (BACKEND_DIR / "static/images").resolve()


def test_runtime_absolute_path_is_preserved():
    absolute = Path("/tmp/ai-platform-square-static")
    assert resolve_runtime_path(str(absolute)) == absolute


def test_runtime_upload_dir_must_match_static_mount_path():
    static_dir = Path("/tmp/static-root")
    invalid_upload_dir = Path("/tmp/custom-uploads")

    with pytest.raises(RuntimeError, match="UPLOAD_DIR must resolve to STATIC_DIR/uploads"):
        validate_static_upload_path_consistency(static_dir, invalid_upload_dir)
