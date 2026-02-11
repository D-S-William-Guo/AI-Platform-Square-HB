import logging
import traceback
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """自定义API错误"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        super().__init__(self.message)


def setup_error_handlers(app: FastAPI) -> None:
    """设置全局错误处理"""
    
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """处理自定义API错误"""
        logger.warning(f"API Error: {exc.error_code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """处理数据库错误"""
        logger.error(f"Database Error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "ERR_DATABASE",
                    "message": "数据库操作失败",
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        """处理通用错误"""
        error_trace = traceback.format_exc()
        logger.error(f"Unhandled Error: {str(exc)}\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "ERR_INTERNAL",
                    "message": "服务器内部错误",
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
