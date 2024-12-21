import asyncio
from typing import Dict, Optional, Set
from datetime import datetime
from pathlib import Path
from ..utils.error_utils import DownloadError
from ..config import MAX_CONCURRENT_DOWNLOADS
from loguru import logger

class DownloadSession:
    """下载会话类"""
    def __init__(self, url: str, session_id: str):
        self.url = url
        self.session_id = session_id
        self.start_time = datetime.now()
        self.progress = 0
        self.speed = 0
        self.eta = 0
        self.status = "pending"
        self.error = None
        self.file_path: Optional[Path] = None
        self._task: Optional[asyncio.Task] = None
        
    @property
    def is_active(self) -> bool:
        """会话是否活跃"""
        return self.status in ("pending", "downloading")
        
    def update_progress(self, downloaded: int, total: int, speed: float, eta: int):
        """更新下载进度"""
        self.progress = (downloaded / total * 100) if total else 0
        self.speed = speed
        self.eta = eta
        
    def complete(self, file_path: Path):
        """完成下载"""
        self.status = "completed"
        self.file_path = file_path
        self.progress = 100
        
    def fail(self, error: str):
        """下载失败"""
        self.status = "failed"
        self.error = error

class DownloadManager:
    """下载管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            self._sessions: Dict[str, DownloadSession] = {}
            self._active_downloads: Set[str] = set()
            self._download_queue = asyncio.Queue()
            self._lock = asyncio.Lock()
            self._initialized = True
            
    async def create_session(self, url: str, session_id: str) -> DownloadSession:
        """
        创建下载会话
        
        Args:
            url: 视频URL
            session_id: 会话ID
            
        Returns:
            下载会话对象
        """
        async with self._lock:
            if session_id in self._sessions:
                raise DownloadError("会话ID已存在")
                
            session = DownloadSession(url, session_id)
            self._sessions[session_id] = session
            await self._download_queue.put(session)
            
            # 启动下载处理器（如果尚未启动）
            if not hasattr(self, '_processor_task'):
                self._processor_task = asyncio.create_task(self._process_downloads())
                
            return session
            
    def get_session(self, session_id: str) -> Optional[DownloadSession]:
        """获取下载会话"""
        return self._sessions.get(session_id)
        
    def remove_session(self, session_id: str):
        """移除下载会话"""
        if session := self._sessions.pop(session_id, None):
            if session.session_id in self._active_downloads:
                self._active_downloads.remove(session.session_id)
                
    async def _process_downloads(self):
        """处理下载队列"""
        while True:
            try:
                # 检查是否可以开始新的下载
                if len(self._active_downloads) >= MAX_CONCURRENT_DOWNLOADS:
                    await asyncio.sleep(1)
                    continue
                    
                # 获取下一个待下载会话
                session = await self._download_queue.get()
                
                if not session.is_active:
                    self._download_queue.task_done()
                    continue
                    
                # 开始下载
                self._active_downloads.add(session.session_id)
                session.status = "downloading"
                
                # 创建下载任务
                session._task = asyncio.create_task(
                    self._download_video(session)
                )
                
            except Exception as e:
                logger.error(f"处理下载队列时发生错误: {str(e)}")
                await asyncio.sleep(1)
                
    async def _download_video(self, session: DownloadSession):
        """
        执行视频下载
        
        Args:
            session: 下载会话
        """
        try:
            from .video_info import VideoInfoService
            
            # 下载视频
            file_path = await VideoInfoService.download_video(session.url)
            
            # 更新会话状态
            session.complete(file_path)
            
        except Exception as e:
            session.fail(str(e))
            logger.error(f"下载视频时发生错误: {str(e)}")
            
        finally:
            # 清理会话
            if session.session_id in self._active_downloads:
                self._active_downloads.remove(session.session_id)
            self._download_queue.task_done()
            
    def get_active_downloads(self) -> int:
        """获取当前活跃下载数"""
        return len(self._active_downloads)
        
    def get_queue_size(self) -> int:
        """获取等待队列大小"""
        return self._download_queue.qsize()
        
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理过期会话"""
        now = datetime.now()
        to_remove = []
        
        for session_id, session in self._sessions.items():
            age = (now - session.start_time).total_seconds() / 3600
            if age > max_age_hours and not session.is_active:
                to_remove.append(session_id)
                
        for session_id in to_remove:
            self.remove_session(session_id) 