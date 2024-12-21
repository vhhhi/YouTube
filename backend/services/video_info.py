import yt_dlp
from typing import Optional, Callable, Dict, Any, Awaitable
from pathlib import Path
from ..models.video import VideoInfo, VideoFormat
from ..utils.file_utils import create_temp_file, move_to_downloads, cleanup_temp_files
from ..utils.error_utils import handle_error, VideoError, DownloadError
from ..utils.url_utils import validate_video_url, extract_video_id
from ..config import MAX_FILE_SIZE
from loguru import logger
import re
import asyncio

class VideoInfoService:
    """视频信息服务类"""
    
    @staticmethod
    async def get_video_info(url: str) -> VideoInfo:
        """
        获取视频信息
        
        Args:
            url: 视频URL
            
        Returns:
            VideoInfo对象
            
        Raises:
            VideoError: 视频相关错误
            ValidationError: URL验证错误
        """
        # 验证URL
        is_valid, error = validate_video_url(url)
        if not is_valid:
            raise VideoError(error)
        
        try:
            # 提取视频ID和平台
            video_id, platform = extract_video_id(url)
            logger.info(f"提取到视频ID: {video_id}, 平台: {platform}")
            
            # 配置yt-dlp选项
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'format': 'best',  # 默认选择最佳质量
                'youtube_include_dash_manifest': True,  # 包括DASH格式
                'youtube_include_hls_manifest': True,   # 包括HLS格式
                'ignoreerrors': True,  # 忽略部分错误继续处理
                'no_color': True       # 禁用颜色输出
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"正在获取视频信息: {url}")
                try:
                    info = ydl.extract_info(url, download=False)
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"yt-dlp下载错误: {str(e)}")
                    raise VideoError(f"获取视频信息失败: {str(e)}")
                except Exception as e:
                    logger.error(f"获取视频信息时发生未知错误: {str(e)}")
                    raise VideoError("获取视频信息时发生未知错误")
                
                if not info:
                    raise VideoError("无法获取视频信息")
                
                formats = []
                for f in info.get('formats', []):
                    # 添加所有格式，包括音频
                    format_note = f.get('format_note', '')
                    if f.get('vcodec') == 'none':
                        format_note = '仅音频'
                    elif f.get('acodec') == 'none':
                        format_note = '仅视频'
                    
                    # 获取分辨率
                    resolution = f.get('resolution', 'unknown')
                    if resolution == 'unknown':
                        width = f.get('width')
                        height = f.get('height')
                        if width and height:
                            resolution = f"{width}x{height}"
                    
                    formats.append(VideoFormat(
                        format_id=f.get('format_id', ''),
                        ext=f.get('ext', ''),
                        resolution=resolution,
                        filesize=f.get('filesize'),
                        vcodec=f.get('vcodec', ''),
                        acodec=f.get('acodec', ''),
                        format_note=format_note,
                        fps=f.get('fps'),
                        tbr=f.get('tbr')
                    ))
                
                if not formats:
                    raise VideoError("未找到任何可用格式")
                
                logger.info(f"成功获取到 {len(formats)} 个格式")
                
                return VideoInfo(
                    id=info.get('id', ''),
                    title=info.get('title', ''),
                    description=info.get('description'),
                    duration=info.get('duration'),
                    thumbnail=info.get('thumbnail'),
                    uploader=info.get('uploader'),
                    formats=formats
                )
                
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp下载错误: {str(e)}")
            raise VideoError(f"下载失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取视频信息时发生错误: {str(e)}")
            raise VideoError(f"获取视频信息失败: {str(e)}")

    @staticmethod
    async def get_video_formats(url: str) -> list[VideoFormat]:
        """
        获取视频可用格式列表
        
        Args:
            url: 视频URL
            
        Returns:
            格式列表
            
        Raises:
            VideoError: 视频相关错误
            ValidationError: URL验证错误
        """
        try:
            video_info = await VideoInfoService.get_video_info(url)
            return video_info.formats
        except Exception as e:
            logger.error(f"获取视频格式失败: {str(e)}")
            raise VideoError(f"获取视频格式失败: {str(e)}")
        
    @staticmethod
    def get_best_format(formats: list[VideoFormat], prefer_quality: str = "720p") -> VideoFormat:
        """
        获取最佳视频格式
        
        Args:
            formats: 格式列表
            prefer_quality: 首选质量
            
        Returns:
            最佳格式
            
        Raises:
            VideoError: 未找到合适的格式
        """
        try:
            if not formats:
                raise VideoError("没有可用的视频格式")
                
            target_formats = [f for f in formats 
                            if f.resolution and prefer_quality in f.resolution]
                            
            if target_formats:
                combined = [f for f in target_formats if f.is_combined]
                if combined:
                    return max(combined, key=lambda x: x.tbr or 0)
                return max(target_formats, key=lambda x: x.tbr or 0)
                
            available_formats = [f for f in formats if f.resolution]
            if not available_formats:
                raise VideoError("未找到有效的视频格式")
                
            target_height = int(prefer_quality.replace('p', ''))
            available_formats.sort(
                key=lambda x: int(x.resolution.split('x')[1]) 
                if 'x' in x.resolution 
                else int(x.resolution.replace('p', '')),
                reverse=True
            )
            
            for fmt in available_formats:
                height = int(fmt.resolution.split('x')[1]) if 'x' in fmt.resolution else int(fmt.resolution.replace('p', ''))
                if height <= target_height:
                    return fmt
                    
            return available_formats[-1]
            
        except Exception as e:
            logger.error(f"选择最佳格式时发生错误: {str(e)}")
            raise handle_error(e)
            
    @staticmethod
    async def download_video(
        url: str, 
        format_id: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> Path:
        """
        下载视频
        
        Args:
            url: 视频URL
            format_id: 可选的格式ID
            progress_callback: 进度回调函数
            
        Returns:
            下载文件路径
            
        Raises:
            VideoError: 视频相关错误
            DownloadError: 下载相关错误
            ValidationError: URL验证错误
        """
        try:
            # 验证URL
            is_valid, error = validate_video_url(url)
            if not is_valid:
                raise VideoError(error)
            
            # 创建临时文件
            temp_file = create_temp_file(suffix=".mp4")
            
            # 创建事件循环
            loop = asyncio.get_event_loop()
            
            def progress_hook(d: Dict[str, Any]):
                """同步进度回调"""
                try:
                    if d['status'] == 'downloading':
                        # 创建一个新的事件循环来运行异步回调
                        async def send_progress():
                            if progress_callback:
                                await progress_callback({
                                    'status': 'downloading',
                                    'downloaded_bytes': d.get('downloaded_bytes', 0),
                                    'total_bytes': d.get('total_bytes', 0),
                                    'speed': d.get('speed', 0),
                                    'eta': d.get('eta', 0),
                                    'filename': d.get('filename', '')
                                })
                        asyncio.run_coroutine_threadsafe(send_progress(), loop)
                    
                    elif d['status'] == 'finished':
                        async def send_processing():
                            if progress_callback:
                                await progress_callback({
                                    'status': 'processing',
                                    'filename': d.get('filename', '')
                                })
                        asyncio.run_coroutine_threadsafe(send_processing(), loop)
                except Exception as e:
                    logger.error(f"进度回调错误: {str(e)}")
            
            ydl_opts = {
                'format': format_id if format_id else 'best',
                'outtmpl': str(temp_file),
                'quiet': False,  # 启用输出以获取进度
                'no_warnings': True,
                'progress_hooks': [progress_hook],
                'noprogress': False,  # 确保显示进度
                'postprocessor_hooks': [progress_hook],  # 添加后处理钩子
                'verbose': True  # 启用详细输出
            }
            
            # 在新线程中运行下载
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            # 在线程池中执行下载
            info = await loop.run_in_executor(None, download)
            
            if not info:
                raise DownloadError("下载失败：无法获取视频信息")
            
            # 检查文件大小
            if temp_file.stat().st_size > MAX_FILE_SIZE:
                temp_file.unlink()
                raise DownloadError("视频文件超过大小限制")
            
            # 移动到下载目录
            final_name = f"{info.get('title', 'video')}.{info.get('ext', 'mp4')}"
            final_path = move_to_downloads(temp_file, final_name)
            
            # 清理过期的临时文件
            cleanup_temp_files()
            
            # 通知下载完成
            if progress_callback:
                await progress_callback({
                    'status': 'complete',
                    'file_path': str(final_path)
                })
            
            return final_path
            
        except Exception as e:
            logger.error(f"下载视频时发生错误: {str(e)}")
            # 确保清理临时文件
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            # 通知下载失败
            if progress_callback:
                await progress_callback({
                    'status': 'error',
                    'error': str(e)
                })
            raise handle_error(e) 