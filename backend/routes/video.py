from fastapi import APIRouter, HTTPException
from typing import Optional, List
from ..services.video_info import VideoInfoService
from ..models.video import VideoInfo, VideoFormat

router = APIRouter()

@router.get("/video/info")
async def get_video_info(url: str) -> VideoInfo:
    """获取视频信息的API端点"""
    try:
        video_info = await VideoInfoService.get_video_info(url)
        if not video_info:
            raise HTTPException(status_code=404, detail="无法获取视频信息")
        return video_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video/best-format")
async def get_best_format(url: str, prefer_quality: Optional[str] = "720p"):
    """获取最佳视频格式的API端点"""
    try:
        video_info = await VideoInfoService.get_video_info(url)
        if not video_info:
            raise HTTPException(status_code=404, detail="无法获取视频信息")
            
        best_format = VideoInfoService.get_best_format(
            video_info.formats, 
            prefer_quality
        )
        
        if not best_format:
            raise HTTPException(status_code=404, detail="未找到合适的视频格式")
            
        return best_format
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video/formats")
async def get_video_formats(url: str) -> List[VideoFormat]:
    """获取视频可用格式列表"""
    try:
        formats = await VideoInfoService.get_video_formats(url)
        if not formats:
            raise HTTPException(status_code=404, detail="无法获取视频格式")
        return formats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/video/info")
async def get_video_info(video_url: str):
    try:
        video_info = await video_service.get_video_info(video_url)
        return {"success": True, "data": video_info}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": "处理视频信息时出错"}
