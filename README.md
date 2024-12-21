# YouTube视频下载器

一个基于FastAPI和yt-dlp的YouTube视频下载工具，支持多种视频格式和实时下载进度显示。

## 功能特点

- 支持YouTube视频下载
- 多种视频格式选择
- 实时下载进度显示
- 并发下载控制
- 文件安全处理
- WebSocket实时通信

## 系统要求

- Python 3.8+
- pip（Python包管理器）
- 操作系统：Windows/Linux/MacOS

## 安装步骤

1. 克隆项目：
```bash
git clone [项目地址]
cd youtube-downloader
```

2. 创建虚拟环境（推荐）：
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 运行项目

1. 启动服务器：
```bash
# 进入backend目录
cd backend

# 启动服务器
python main.py
```

2. 访问网页：
   - 打开浏览器
   - 访问 http://localhost:8000

## 使用说明

1. 在网页输入YouTube视频URL
2. 选择需要的视频格式
3. 点击下载按钮
4. 等待下载完成

## 目录结构

```
youtube-downloader/
├── backend/
│   ├── main.py          # 主入口文件
│   ├── config.py        # 配置文件
│   ├── models/          # 数据模型
│   ├── routes/          # 路由处理
│   ├── services/        # 业务服务
│   └── utils/           # 工具函数
├── frontend/
│   ├── static/          # 静态文件
│   └── templates/       # 模板文件
├── downloads/           # 下载文件目录
├── requirements.txt     # 项目依赖
└── README.md           # 项目说明
```

## 注意事项

1. 确保有足够的磁盘空间
2. 下载大文件时可能需要较长时间
3. 某些视频可能因版权限制无法下载
4. 请遵守YouTube的服务条款

## 常见问题

1. 如果遇到依赖安装问题，可以尝试：
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

2. 如果出现权限问题：
   - Windows: 以管理员身份运行命令提示符
   - Linux/MacOS: 使用sudo运行命令

3. 如果无法下载视频：
   - 检查视频URL是否正确
   - 确认视频是否可公开访问
   - 检查网络连接

## 技术栈

- 后端：FastAPI, yt-dlp, WebSocket
- 前端：HTML, JavaScript, TailwindCSS
- 工具：uvicorn, loguru

## 贡献指南

欢迎提交Issue和Pull Request来改��项目。

## 许可证

MIT License 