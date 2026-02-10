import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class VenvReader:
    """虚拟环境读取工具类"""
    
    def __init__(self, venv_path: Optional[Path] = None):
        """
        初始化虚拟环境读取器
        
        Args:
            venv_path: 虚拟环境路径，如果不指定则自动检测
        """
        if venv_path:
            self.venv_path = venv_path
        else:
            self.venv_path = self._detect_venv_path()
        
    def _detect_venv_path(self) -> Path:
        """
        自动检测虚拟环境路径
        
        Returns:
            虚拟环境路径
        """
        # 首先检查当前脚本所在目录的 .venv 目录
        current_dir = Path(__file__).parent.parent
        venv_path = current_dir / ".venv"
        
        if venv_path.exists() and venv_path.is_dir():
            return venv_path
        
        # 检查系统环境变量中的 VIRTUAL_ENV
        if "VIRTUAL_ENV" in os.environ:
            venv_path = Path(os.environ["VIRTUAL_ENV"])
            if venv_path.exists() and venv_path.is_dir():
                return venv_path
        
        # 检查 sys.prefix
        sys_prefix = Path(sys.prefix)
        if sys_prefix.name == ".venv" or "venv" in sys_prefix.name:
            if sys_prefix.exists() and sys_prefix.is_dir():
                return sys_prefix
        
        # 默认返回当前目录的 .venv
        return current_dir / ".venv"
    
    def is_valid_venv(self) -> bool:
        """
        检查虚拟环境是否有效
        
        Returns:
            是否为有效虚拟环境
        """
        if not self.venv_path.exists() or not self.venv_path.is_dir():
            return False
        
        # 检查关键目录和文件
        if sys.platform == "win32":
            # Windows 环境
            scripts_dir = self.venv_path / "Scripts"
            python_exe = scripts_dir / "python.exe"
            return scripts_dir.exists() and python_exe.exists()
        else:
            # Unix/Linux 环境
            bin_dir = self.venv_path / "bin"
            python_exe = bin_dir / "python"
            return bin_dir.exists() and python_exe.exists()
    
    def get_venv_info(self) -> Dict[str, any]:
        """
        获取虚拟环境信息
        
        Returns:
            虚拟环境信息字典
        """
        info = {
            "path": str(self.venv_path),
            "is_valid": self.is_valid_venv(),
            "python_version": None,
            "pip_version": None,
            "dependencies": []
        }
        
        if info["is_valid"]:
            # 获取 Python 版本
            try:
                import subprocess
                if sys.platform == "win32":
                    python_exe = self.venv_path / "Scripts" / "python.exe"
                else:
                    python_exe = self.venv_path / "bin" / "python"
                
                result = subprocess.run(
                    [str(python_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    info["python_version"] = result.stdout.strip()
            except Exception as e:
                pass
            
            # 获取 pip 版本
            try:
                import subprocess
                if sys.platform == "win32":
                    pip_exe = self.venv_path / "Scripts" / "pip.exe"
                else:
                    pip_exe = self.venv_path / "bin" / "pip"
                
                result = subprocess.run(
                    [str(pip_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    info["pip_version"] = result.stdout.strip()
            except Exception as e:
                pass
            
            # 获取依赖列表
            try:
                import subprocess
                if sys.platform == "win32":
                    pip_exe = self.venv_path / "Scripts" / "pip.exe"
                else:
                    pip_exe = self.venv_path / "bin" / "pip"
                
                result = subprocess.run(
                    [str(pip_exe), "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    import json
                    info["dependencies"] = json.loads(result.stdout)
            except Exception as e:
                pass
        
        return info
    
    def get_venv_python_path(self) -> Optional[Path]:
        """
        获取虚拟环境中 Python 可执行文件的路径
        
        Returns:
            Python 可执行文件路径
        """
        if not self.is_valid_venv():
            return None
        
        if sys.platform == "win32":
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"
        
        if python_exe.exists():
            return python_exe
        return None
    
    def get_venv_pip_path(self) -> Optional[Path]:
        """
        获取虚拟环境中 pip 可执行文件的路径
        
        Returns:
            pip 可执行文件路径
        """
        if not self.is_valid_venv():
            return None
        
        if sys.platform == "win32":
            pip_exe = self.venv_path / "Scripts" / "pip.exe"
        else:
            pip_exe = self.venv_path / "bin" / "pip"
        
        if pip_exe.exists():
            return pip_exe
        return None
    
    def get_venv_site_packages(self) -> Optional[Path]:
        """
        获取虚拟环境中 site-packages 目录的路径
        
        Returns:
            site-packages 目录路径
        """
        if not self.is_valid_venv():
            return None
        
        if sys.platform == "win32":
            site_packages = self.venv_path / "Lib" / "site-packages"
        else:
            # 对于 Unix/Linux，需要确定 Python 版本
            python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
            site_packages = self.venv_path / "lib" / python_version / "site-packages"
        
        if site_packages.exists() and site_packages.is_dir():
            return site_packages
        return None


# 创建全局实例
venv_reader = VenvReader()
