import re
from typing import Tuple
from urllib.parse import urlparse
from .error_utils import ValidationError

# 支持的视频平台
SUPPORTED_PLATFORMS = {
    'youtube.com': r'^https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)[a-zA-Z0-9_-]+)',
    'youtu.be': r'^https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[a-zA-Z0-9_-]+',
    'bilibili.com': r'^https?://(?:www\.)?bilibili\.com/video/[a-zA-Z0-9]+',
}

def validate_video_url(url: str) -> Tuple[bool, str]:
    """
    验证视频URL
    
    Args:
        url: 视频URL
        
    Returns:
        (是否有效, 错误信息)
    """
    if not url:
        return False, "URL不能为空"
        
    # 基本URL格式验证
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False, "无效的URL格式"
    except Exception:
        return False, "无效的URL格式"
        
    # 检查是否是支持的平台
    domain = parsed.netloc.replace('www.', '')
    platform = next((p for p in SUPPORTED_PLATFORMS.keys() if p in domain), None)
    
    if not platform:
        return False, "不支持的视频平台"
        
    # 检查URL格式是否符合平台规则
    pattern = SUPPORTED_PLATFORMS[platform]
    if not re.match(pattern, url):
        return False, "无效的视频URL格式"
        
    return True, ""

def extract_video_id(url: str) -> Tuple[str, str]:
    """
    从URL中提取视频ID和平台
    
    Args:
        url: 视频URL
        
    Returns:
        (视频ID, 平台名称)
        
    Raises:
        ValidationError: URL无效时抛出
    """
    is_valid, error = validate_video_url(url)
    if not is_valid:
        raise ValidationError(error)
        
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    
    # YouTube
    if 'youtube.com' in domain or 'youtu.be' in domain:
        if 'youtube.com' in domain:
            # 检查是否是shorts
            shorts_id = re.search(r'shorts/([a-zA-Z0-9_-]+)', url)
            if shorts_id:
                return shorts_id.group(1), 'youtube'
            # 从查询参数中获取
            video_id = re.search(r'v=([a-zA-Z0-9_-]+)', url)
            if video_id:
                return video_id.group(1), 'youtube'
        else:
            # 从路径中获取
            video_id = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
            if video_id:
                return video_id.group(1), 'youtube'
                
    # Bilibili
    elif 'bilibili.com' in domain:
        video_id = re.search(r'video/([a-zA-Z0-9]+)', url)
        if video_id:
            return video_id.group(1), 'bilibili'
            
    raise ValidationError("无法从URL中提取视频ID") 