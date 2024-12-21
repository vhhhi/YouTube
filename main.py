from fastapi import FastAPI, WebSocket, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import os
import asyncio
import functools

# 修改 yt-dlp 的导入方式
try:
    import yt_dlp
except ImportError:
    raise ImportError("请确保已安装 yt-dlp: pip install yt-dlp")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 静态文件和下载目录
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# 定义下载目录
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储下载进度的全局变量
download_progress = {}

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'no_color': True,
        'postprocessors': [],
        'prefer_ffmpeg': False,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Error in get_video_info: {str(e)}")
        return None

async def download_video(url: str, websocket: WebSocket):
    loop = asyncio.get_event_loop()
    progress_queue = asyncio.Queue()
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            progress = {
                'status': 'downloading',
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes': d.get('total_bytes', 0),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0)
            }
            loop.call_soon_threadsafe(progress_queue.put_nowait, progress)
        elif d['status'] == 'finished':
            loop.call_soon_threadsafe(progress_queue.put_nowait, {'status': 'finished'})

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'noprogress': False,
        'noplaylist': True
    }
    
    try:
        download_task = loop.run_in_executor(None, functools.partial(yt_dlp.YoutubeDL(ydl_opts).download, [url]))
        
        while True:
            try:
                progress = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                await websocket.send_json(progress)
                if progress['status'] == 'finished':
                    break
            except asyncio.TimeoutError:
                if download_task.done():
                    break
                continue
            
        await download_task
        
        # 获取下载后的视频信息
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_path = ydl.prepare_filename(info)
            
            if os.path.exists(video_path):
                video_info = {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'description': info.get('description'),
                    'filepath': video_path,
                    'filesize': os.path.getsize(video_path)
                }
                
                save_video_info(video_info)
                await websocket.send_json({"status": "complete", "info": video_info})
            else:
                await websocket.send_json({"status": "error", "message": "Download failed"})
            
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})

def save_video_info(info):
    videos_file = DOWNLOAD_DIR / "videos.json"
    videos = []
    if videos_file.exists():
        with open(videos_file) as f:
            videos = json.load(f)
    videos.append(info)
    with open(videos_file, "w") as f:
        json.dump(videos, f)

def get_downloaded_videos():
    videos_file = DOWNLOAD_DIR / "videos.json"
    if videos_file.exists():
        with open(videos_file) as f:
            return json.load(f)
    return []

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    videos = get_downloaded_videos()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "videos": videos}
    )

@app.websocket("/ws/download")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            url = await websocket.receive_text()
            await download_video(url, websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}") 