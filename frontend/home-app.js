/**
 * 首页应用
 * 使用 Vue 3
 */

const { createApp } = Vue;

// API 基础地址 - 自动检测可用端口
let API_BASE_URL = 'http://127.0.0.1:8001';

// 尝试检测后端端口
async function detectBackendPort() {
    const ports = [8001, 8000, 8002, 8003, 8004, 8005];
    
    for (const port of ports) {
        try {
            const url = `http://127.0.0.1:${port}/health`;
            const response = await axios.get(url, { timeout: 1000 });
            if (response.data.status === 'healthy') {
                API_BASE_URL = `http://127.0.0.1:${port}`;
                console.log(`✅ 检测到后端运行在端口 ${port}`);
                return true;
            }
        } catch (e) {
            // 继续尝试下一个端口
        }
    }
    
    console.warn('⚠️ 无法检测到后端服务');
    return false;
}

createApp({
    data() {
        return {
            backendOnline: false,  // 后端是否在线
            checking: true         // 是否正在检查
        }
    },
    
    methods: {
        /**
         * 检查后端是否在线
         */
        async checkBackend() {
            this.checking = true;
            this.backendOnline = await detectBackendPort();
            this.checking = false;
        },
        
        /**
         * 跳转到爬虫页面
         */
        async goToCrawler() {
            // 先检查后端是否在线
            if (!this.backendOnline) {
                alert('后端服务未启动，请先启动后端服务！\n\n运行 start_backend.bat 或 python backend/api.py');
                return;
            }
            
            // 跳转到爬虫页面
            window.location.href = 'index.html';
        },
        
        /**
         * 显示即将上线提示
         */
        showComingSoon() {
            alert('该功能即将上线，敬请期待！');
        }
    },
    
    async mounted() {
        console.log('数据采集平台首页已加载');
        
        // 检查后端状态
        await this.checkBackend();
        
        // 每15秒检查一次后端状态
        setInterval(() => {
            this.checkBackend();
        }, 15000);
    }
}).mount('#app');
