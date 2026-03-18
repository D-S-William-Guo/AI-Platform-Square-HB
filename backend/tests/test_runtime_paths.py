from pathlib import Path

import app.main as main_module
from fastapi.responses import FileResponse
import pytest

from app.config import BACKEND_DIR, resolve_runtime_path
from app.main import get_frontend_index_file, resolve_frontend_asset, serve_frontend_app, serve_frontend_index


def test_runtime_relative_paths_are_anchored_to_backend_dir():
    assert resolve_runtime_path("static") == (BACKEND_DIR / "static").resolve()
    assert resolve_runtime_path("static/uploads") == (BACKEND_DIR / "static/uploads").resolve()
    assert resolve_runtime_path("static/images") == (BACKEND_DIR / "static/images").resolve()


def test_runtime_absolute_path_is_preserved():
    absolute = Path("/tmp/ai-platform-square-static")
    assert resolve_runtime_path(str(absolute)) == absolute


def test_frontend_build_paths_are_resolved_from_dist(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    asset_dir = dist_dir / "assets"
    asset_dir.mkdir(parents=True)
    index_file = dist_dir / "index.html"
    asset_file = asset_dir / "app.js"
    index_file.write_text("<html>ok</html>", encoding="utf-8")
    asset_file.write_text("console.log('ok')", encoding="utf-8")

    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)

    assert get_frontend_index_file() == index_file
    assert resolve_frontend_asset("assets/app.js") == asset_file
    assert resolve_frontend_asset("../secrets.txt") is None


def test_frontend_routes_fallback_to_index(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    asset_dir = dist_dir / "assets"
    asset_dir.mkdir(parents=True)
    index_file = dist_dir / "index.html"
    asset_file = asset_dir / "bundle.js"
    index_file.write_text("<html>spa</html>", encoding="utf-8")
    asset_file.write_text("console.log('bundle')", encoding="utf-8")

    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)

    root_response = serve_frontend_index()
    route_response = serve_frontend_app("ranking-management")
    asset_response = serve_frontend_app("assets/bundle.js")

    assert isinstance(root_response, FileResponse)
    assert Path(root_response.path) == index_file
    assert isinstance(route_response, FileResponse)
    assert Path(route_response.path) == index_file
    assert isinstance(asset_response, FileResponse)
    assert Path(asset_response.path) == asset_file

    with pytest.raises(Exception) as exc_info:
        serve_frontend_app("api/missing")
    assert getattr(exc_info.value, "status_code", None) == 404
