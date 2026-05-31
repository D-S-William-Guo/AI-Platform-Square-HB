"""元数据路由: health, enums, venv info."""

from fastapi import APIRouter, Depends

from ..config import (
    get_app_category_options,
    is_development_environment,
    settings,
)
from ..dependencies import require_development_mode
from ..venv_utils import venv_reader

router = APIRouter(prefix=settings.api_prefix)

APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}
APP_CATEGORY_OPTIONS = get_app_category_options(settings)
APP_DIFFICULTY_VALUES = {"Low", "Medium", "High"}
METRIC_TYPES = {"composite", "growth_rate", "likes"}
VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/meta/enums")
def list_enums():
    return {
        "app_status": sorted(APP_STATUS_VALUES),
        "app_category": APP_CATEGORY_OPTIONS,
        "app_difficulty": sorted(APP_DIFFICULTY_VALUES),
        "ranking_metric_type": sorted(METRIC_TYPES),
        "value_dimension": sorted(VALUE_DIMENSIONS),
        "data_level": sorted(DATA_LEVEL_VALUES),
    }


@router.get("/venv/info")
def get_venv_info():
    """获取虚拟环境信息"""
    require_development_mode()
    return venv_reader.get_venv_info()


@router.get("/venv/python-path")
def get_venv_python_path():
    """获取虚拟环境中Python可执行文件的路径"""
    require_development_mode()
    python_path = venv_reader.get_venv_python_path()
    if python_path:
        return {"python_path": str(python_path)}
    return {"error": "Virtual environment not found or invalid"}


@router.get("/venv/site-packages")
def get_venv_site_packages():
    """获取虚拟环境中site-packages目录的路径"""
    require_development_mode()
    site_packages = venv_reader.get_venv_site_packages()
    if site_packages:
        return {"site_packages_path": str(site_packages)}
    return {"error": "Virtual environment not found or invalid"}
