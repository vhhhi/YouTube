/**
 * 格式化字节大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化后的大小
 */
export function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '未知';
    
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * 格式化下载速度
 * @param {number} bytesPerSecond 每秒字节数
 * @returns {string} 格式化后的速度
 */
export function formatSpeed(bytesPerSecond) {
    if (!bytesPerSecond || bytesPerSecond === 0) return '计算中...';
    
    const mbps = bytesPerSecond * 8 / 1024 / 1024;
    return `${mbps.toFixed(2)} Mbps`;
}

/**
 * 格式化时间（秒转MM:SS）
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时间
 */
export function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * 格式化剩余时间
 * @param {number} seconds - 剩余秒数
 * @returns {string} 格式化后的时间
 */
export function formatETA(seconds) {
    if (seconds === undefined || seconds === Infinity) return '计算中...';
    if (seconds < 60) return `${seconds}秒`;
    return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
}

/**
 * 验证YouTube URL
 * @param {string} url - 视频URL
 * @returns {boolean} 是否为有效的YouTube URL
 */
function validateYoutubeUrl(url) {
    const patterns = [
        /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=)?([a-zA-Z0-9_-]{11})/,
        /^(https?:\/\/)?(www\.)?(youtube\.com)\/shorts\/([a-zA-Z0-9_-]{11})/
    ];
    
    return patterns.some(pattern => pattern.test(url));
} 