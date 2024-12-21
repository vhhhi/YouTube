import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"

# 确保下载目录存在
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
DEBUG = True

# 跨域配置
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# 下载配置
MAX_CONCURRENT_DOWNLOADS = 3  # 最大同时下载数
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
TEMP_DIR = DOWNLOADS_DIR / "temp"  # 临时文件目录
os.makedirs(TEMP_DIR, exist_ok=True)

# 视频格式配置
DEFAULT_PREFERRED_QUALITY = "720p"
SUPPORTED_FORMATS = ["mp4", "webm", "mkv"]

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "logs" / "app.log"
os.makedirs(LOG_FILE.parent, exist_ok=True)

# 安全配置
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 2  # 2GB
ALLOWED_HOSTS = ["*"]
