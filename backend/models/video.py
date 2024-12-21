from typing import List, Optional
from pydantic import BaseModel

class VideoFormat(BaseModel):
    """视频格式信息模型"""
    format_id: str
    ext: str  # 文件扩展名
    resolution: str  # 分辨率
    filesize: Optional[int]  # 文件大小(字节)
    vcodec: str  # 视频编码
    acodec: str  # 音频编码
    format_note: str  # 格式说明
    fps: Optional[float]  # 帧率
    tbr: Optional[float]  # 总比特率
    
    @property
    def is_video_only(self) -> bool:
        """是否仅视频流"""
        return self.acodec == "none" and self.vcodec != "none"
    
    @property
    def is_audio_only(self) -> bool:
        """是否仅音频流"""
        return self.vcodec == "none" and self.acodec != "none"
    
    @property
    def is_combined(self) -> bool:
        """是否音视频组合"""
        return self.vcodec != "none" and self.acodec != "none"

class VideoInfo(BaseModel):
    """视频信息模型"""
    id: str  # 视频ID
    title: str  # 标题
    description: Optional[str]  # 描述
    duration: Optional[int]  # 时长(秒)
    thumbnail: Optional[str]  # 缩略图URL
    uploader: Optional[str]  # 上传者
    formats: List[VideoFormat]  # 可用格式列表
    
    def get_formats_by_type(self, format_type: str) -> List[VideoFormat]:
        """获取指定类型的格式列表
        
        Args:
            format_type: 格式类型 ("video_only", "audio_only", "combined")
            
        Returns:
            符合条件的格式列表
        """
        if format_type == "video_only":
            return [f for f in self.formats if f.is_video_only]
        elif format_type == "audio_only":
            return [f for f in self.formats if f.is_audio_only]
        elif format_type == "combined":
            return [f for f in self.formats if f.is_combined]
        else:
            return self.formats
