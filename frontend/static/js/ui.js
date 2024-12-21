import VideoAPI from './api.js';
import { formatBytes, formatSpeed } from './utils.js';

let currentFormats = [];

export function initUI() {
    const urlInput = document.getElementById('videoUrl');
    const checkButton = document.getElementById('checkUrl');
    const downloadButton = document.getElementById('download');
    const formatSelect = document.getElementById('formatSelect');
    const formatsDropdown = document.getElementById('formats');
    const formatInfo = document.getElementById('formatInfo');
    const progress = document.getElementById('progress');
    const progressInfo = document.getElementById('progressInfo');

    // 当选择格式时启用下载按钮
    formatsDropdown.addEventListener('change', () => {
        const selectedFormat = currentFormats.find(f => f.format_id === formatsDropdown.value);
        downloadButton.disabled = !formatsDropdown.value;
        
        if (selectedFormat) {
            formatInfo.textContent = `分辨率: ${selectedFormat.resolution}, 
                                    编码: ${selectedFormat.vcodec}/${selectedFormat.acodec}, 
                                    大小: ${formatBytes(selectedFormat.filesize)}`;
        } else {
            formatInfo.textContent = '';
        }
    });

    // 获取格式按钮点击事件
    checkButton.addEventListener('click', async () => {
        console.log('点击获取格式按钮');
        const url = urlInput.value.trim();
        if (!url) {
            alert('请输入视频URL');
            return;
        }

        try {
            console.log('开始获取格式，URL:', url);
            checkButton.disabled = true;
            checkButton.textContent = '获取中...';
            
            // 获取可用格式
            currentFormats = await VideoAPI.getVideoFormats(url);
            console.log('获取到的格式:', currentFormats);
            
            // 清空并填充格式下拉框
            formatsDropdown.innerHTML = '<option value="">请选择格式...</option>';
            currentFormats.forEach(format => {
                const option = document.createElement('option');
                option.value = format.format_id;
                // 提取分辨率数字部分
                const resolution = format.resolution.split('x')[1] || format.resolution;
                option.textContent = `${resolution}p - ${format.ext}`;
                formatsDropdown.appendChild(option);
            });

            // 显示格式选择区域
            formatSelect.style.display = 'block';
            
        } catch (error) {
            console.error('获取格式失败:', error);
            alert(error.message);
        } finally {
            checkButton.disabled = false;
            checkButton.textContent = '获取格式';
        }
    });

    // 下载按钮点击事件
    downloadButton.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        const formatId = formatsDropdown.value;
        
        if (!url || !formatId) {
            alert('请选择下载格式');
            return;
        }

        try {
            progress.style.display = 'block';
            downloadButton.disabled = true;
            progressInfo.textContent = '准备下载...';
            
            const ws = await VideoAPI.startDownload(url, formatId);
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.status === 'downloading') {
                    const percent = (data.downloaded_bytes / data.total_bytes * 100).toFixed(1);
                    const speed = formatSpeed(data.speed);
                    const eta = data.eta ? `${data.eta}秒` : '计算中';
                    
                    progressInfo.textContent = 
                        `下载进度: ${percent}% | 速度: ${speed} | 剩余时间: ${eta}`;
                } else if (data.status === 'complete') {
                    progressInfo.textContent = '下载完成！';
                    downloadButton.disabled = false;
                    ws.close();
                } else if (data.status === 'error') {
                    progressInfo.textContent = `错误: ${data.message}`;
                    downloadButton.disabled = false;
                    ws.close();
                }
            };
        } catch (error) {
            alert(error.message);
            progress.style.display = 'none';
            downloadButton.disabled = false;
        }
    });
} 