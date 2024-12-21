import os
import uuid
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes import video
from backend.services.websocket_manager import WebSocketManager
from backend.config import (
    CORS_ORIGINS, 
    CORS_ALLOW_CREDENTIALS, 
    CORS_ALLOW_METHODS, 
    CORS_ALLOW_HEADERS,
    DOWNLOADS_DIR
)
from loguru import logger

# 创建FastAPI应用
app = FastAPI(
    title="YouTube视频下载器",
    description="一个简单的YouTube视频下载工具",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# 确保目录存在
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 静态文件和模板设置
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# WebSocket管理器
ws_manager = WebSocketManager()

# 注册路由
app.include_router(video.router, prefix="/api")

@app.get("/")
async def read_root(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/download")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket下载端点"""
    # 生成客户端ID
    client_id = str(uuid.uuid4())
    
    try:
        # 建立连接
        await ws_manager.connect(websocket, client_id)
        logger.info(f"新的WebSocket连接: {client_id}")
        
        # 处理消息
        while True:
            message = await websocket.receive_text()
            await ws_manager.handle_client_message(client_id, message)
            
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        
    finally:
        # 断开连接
        ws_manager.disconnect(client_id)
        logger.info(f"WebSocket连接断开: {client_id}")

if __name__ == "__main__":
    import uvicorn
    # 启动服务器
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 