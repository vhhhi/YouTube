from typing import Any, Optional, Dict, Type
from fastapi import HTTPException
from loguru import logger
import traceback

class AppError(Exception):
    """应用程序错误基类"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class VideoError(AppError):
    """视频相关错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)

class DownloadError(AppError):
    """下载相关错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

class ValidationError(AppError):
    """数据验证错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)

ERROR_MAPPINGS = {
    "Video unavailable": ("视频不可用或已被删除", VideoError),
    "Private video": ("这是一个私密视频", VideoError),
    "Sign in": ("需要登录才能访问此视频", VideoError),
    "This video is not available": ("视频不可用", VideoError),
    "Video too large": ("视频文件太大", DownloadError),
    "Unable to download": ("无法下载视频", DownloadError),
    "Invalid URL": ("无效的视频地址", ValidationError),
}

def handle_error(error: Exception) -> AppError:
    """
    处理异常，转换为应用程序错误
    
    Args:
        error: 原始异常
        
    Returns:
        应用程序错误
    """
    error_message = str(error)
    error_type = type(error).__name__
    
    # 记录错误详情
    logger.error(f"错误类型: {error_type}")
    logger.error(f"错误信息: {error_message}")
    logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")
    
    # 匹配已知错误模式
    for pattern, (message, error_class) in ERROR_MAPPINGS.items():
        if pattern.lower() in error_message.lower():
            return error_class(message, {
                'original_error': error_message,
                'error_type': error_type
            })
    
    # 默认错误处理
    if isinstance(error, AppError):
        return error
    
    return AppError(
        message="服务器内部错误",
        status_code=500,
        details={
            'original_error': error_message,
            'error_type': error_type
        }
    )

def raise_http_error(error: AppError):
    """
    将应用程序错误转换为HTTP异常
    
    Args:
        error: 应用程序错误
    
    Raises:
        HTTPException: FastAPI HTTP异常
    """
    raise HTTPException(
        status_code=error.status_code,
        detail={
            'message': error.message,
            'details': error.details
        }
    )

def format_error_response(error: AppError) -> Dict[str, Any]:
    """
    格式化错误响应
    
    Args:
        error: 应用程序错误
        
    Returns:
        格式化的错误响应
    """
    return {
        'error': {
            'message': error.message,
            'code': error.status_code,
            'details': error.details
        }
    } 