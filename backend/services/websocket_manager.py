import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
from .download_manager import DownloadManager
from ..utils.error_utils import handle_error
from loguru import logger

class WebSocketManager:
    """WebSocket连接管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            self._active_connections: Dict[str, WebSocket] = {}
            self._download_manager = DownloadManager()
            self._initialized = True
            
    async def connect(self, websocket: WebSocket, client_id: str):
        """建立WebSocket连接"""
        await websocket.accept()
        self._active_connections[client_id] = websocket
        logger.info(f"WebSocket客户端连接: {client_id}")
        
    def disconnect(self, client_id: str):
        """断开WebSocket连接"""
        if client_id in self._active_connections:
            del self._active_connections[client_id]
            logger.info(f"WebSocket客户端断开: {client_id}")
            
    async def send_message(self, client_id: str, message: dict):
        """发送消息给指定客户端"""
        if websocket := self._active_connections.get(client_id):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                self.disconnect(client_id)
                
    async def handle_download_request(self, client_id: str, url: str, format_id: Optional[str] = None):
        """处理下载请求"""
        try:
            # 创建下载会话
            session = await self._download_manager.create_session(url, client_id)
            
            # 定义进度回调
            async def progress_callback(data: dict):
                if data['status'] == 'downloading':
                    await self.send_message(client_id, {
                        'status': 'downloading',
                        'downloaded_bytes': data['downloaded_bytes'],
                        'total_bytes': data['total_bytes'],
                        'speed': data['speed'],
                        'eta': data['eta']
                    })
                elif data['status'] == 'completed':
                    await self.send_message(client_id, {
                        'status': 'complete',
                        'file_path': data['file_path']
                    })
                elif data['status'] == 'error':
                    await self.send_message(client_id, {
                        'status': 'error',
                        'message': data['error']
                    })
                
            # 开始下载
            from .video_info import VideoInfoService
            await VideoInfoService.download_video(
                url,
                format_id=format_id,
                progress_callback=progress_callback
            )
            
        except Exception as e:
            error = handle_error(e)
            await self.send_message(client_id, {
                'status': 'error',
                'message': str(error)
            })
            
    async def handle_client_message(self, client_id: str, message: str):
        """处理客户端消息"""
        try:
            # 尝试解析JSON格式
            try:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'download':
                    url = data.get('url')
                    format_id = data.get('format_id')
                    if not url:
                        raise ValueError("缺少URL参数")
                    await self.handle_download_request(client_id, url, format_id)
                    
                elif message_type == 'cancel':
                    session_id = data.get('session_id')
                    if session_id:
                        self._download_manager.remove_session(session_id)
                        await self.send_message(client_id, {
                            'status': 'cancelled'
                        })
                        
                else:
                    await self.send_message(client_id, {
                        'status': 'error',
                        'message': '不支持的消息类型'
                    })
                    
            except json.JSONDecodeError:
                # 如果不是JSON格式，则视为直接的URL字符串
                await self.handle_download_request(client_id, message)
                
        except Exception as e:
            error = handle_error(e)
            await self.send_message(client_id, {
                'status': 'error',
                'message': str(error)
            }) 