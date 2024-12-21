import os
import re
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from ..config import TEMP_DIR, DOWNLOADS_DIR

def sanitize_filename(filename: str) -> str:
    """
    安全化文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    # 移除不安全字符，只保留字母、数字、下划线、横线和点
    safe_filename = re.sub(r'[^\w\-\.]', '_', filename)
    # 确保文件名不以点开始（避免隐藏文件）
    safe_filename = safe_filename.lstrip('.')
    # 限制文件名长度
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:255-len(ext)] + ext
    return safe_filename or 'unnamed_file'

def get_safe_filepath(filename: str, directory: Path = DOWNLOADS_DIR) -> Path:
    """
    获取安全的文件路径，避免文件名冲突
    
    Args:
        filename: 原始文件名
        directory: 目标目录
        
    Returns:
        安全的文件路径
    """
    safe_filename = sanitize_filename(filename)
    filepath = directory / safe_filename
    
    # 如果文件已存在，添加数字后缀
    if filepath.exists():
        name, ext = os.path.splitext(safe_filename)
        counter = 1
        while (directory / f"{name}_{counter}{ext}").exists():
            counter += 1
        filepath = directory / f"{name}_{counter}{ext}"
    
    return filepath

def create_temp_file(prefix: str = "", suffix: str = "") -> Path:
    """
    创建临时文件
    
    Args:
        prefix: 文件名前缀
        suffix: 文件扩展名
        
    Returns:
        临时文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}{suffix}" if prefix else f"temp_{timestamp}{suffix}"
    return TEMP_DIR / sanitize_filename(filename)

def cleanup_temp_files(max_age: Optional[timedelta] = None):
    """
    清理临时文件
    
    Args:
        max_age: 文件最大保留时间，默认24小时
    """
    if max_age is None:
        max_age = timedelta(hours=24)
        
    current_time = datetime.now()
    
    try:
        for file in TEMP_DIR.iterdir():
            if not file.is_file():
                continue
                
            file_age = current_time - datetime.fromtimestamp(file.stat().st_mtime)
            if file_age > max_age:
                try:
                    file.unlink()
                except Exception as e:
                    print(f"清理临时文件失败 {file}: {str(e)}")
    except Exception as e:
        print(f"清理临时文件时发生错误: {str(e)}")

def move_to_downloads(temp_file: Path, final_name: str) -> Path:
    """
    将临时文件移动到下载目录
    
    Args:
        temp_file: 临时文件路径
        final_name: 最终文件名
        
    Returns:
        最终文件路径
    """
    if not temp_file.exists():
        raise FileNotFoundError(f"临时文件不存在: {temp_file}")
        
    final_path = get_safe_filepath(final_name)
    shutil.move(str(temp_file), str(final_path))
    return final_path 