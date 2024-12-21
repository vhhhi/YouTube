class VideoAPI {
    /**
     * 获取视频信息
     * @param {string} url - 视频URL
     * @returns {Promise<Object>} 视频信息
     */
    static async getVideoInfo(url) {
        try {
            const response = await fetch(`/api/video/info?url=${encodeURIComponent(url)}`);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '获取视频信息失败');
            }
            return await response.json();
        } catch (error) {
            throw new Error(`API错误: ${error.message}`);
        }
    }

    /**
     * 获取视频格式列表
     * @param {string} url - 视频URL
     * @returns {Promise<Array>} 格式列表
     */
    static async getVideoFormats(url) {
        try {
            const response = await fetch(`/api/video/formats?url=${encodeURIComponent(url)}`);
            if (!response.ok) {
                const error = await response.json();
                console.error('API错误响应:', error);
                throw new Error(error.detail || '获取视频格式失败');
            }
            const data = await response.json();
            console.log('获取到的格式数据:', data);
            return data;
        } catch (error) {
            console.error('获取格式失败:', error);
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                throw new Error('无法连接到服务器，请检查网络连接');
            }
            throw error;
        }
    }

    /**
     * 创建WebSocket连接
     * @returns {Promise<WebSocket>}
     */
    static createWebSocket() {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket(`ws://${window.location.host}/ws/download`);
            
            ws.onopen = () => {
                console.log('WebSocket连接已建立');
                resolve(ws);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                reject(error);
            };
            
            ws.onclose = () => {
                console.log('WebSocket连接已关闭');
            };
        });
    }

    /**
     * 开始下载视频
     * @param {string} url - 视频URL
     * @param {string} formatId - 可选的格式ID
     */
    static async startDownload(url, formatId = null) {
        try {
            const ws = await this.createWebSocket();
            
            // 发送包含format_id的JSON消息
            ws.send(JSON.stringify({
                type: 'download',
                url: url,
                format_id: formatId
            }));
            
            return ws;
        } catch (error) {
            throw new Error(`下载错误: ${error.message}`);
        }
    }
}

// 导出API类
export default VideoAPI; 