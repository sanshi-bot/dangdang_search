/**
 * 当当网图书爬虫前端应用
 * 使用 Vue 3 + Axios
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
                return port;
            }
        } catch (e) {
            // 继续尝试下一个端口
        }
    }
    
    console.warn('⚠️ 无法检测到后端服务，使用默认端口 8001');
    return 8001;
}

createApp({
    data() {
        return {
            keyword: '',           // 搜索关键词
            maxBooks: 20,          // 爬取数量（默认20本）
            proxy: '',             // 代理地址
            books: [],            // 图书列表
            loading: false,       // 加载状态
            error: '',           // 错误信息
            searched: false,     // 是否已搜索
            currentKeyword: '',  // 当前显示的关键词
            dataSource: '',      // 数据来源
            backendOnline: true, // 后端是否在线
            heartbeatTimer: null, // 心跳检测定时器
            currentPage: 1,      // 当前页码
            pageSize: 10         // 每页显示数量
        }
    },
    
    computed: {
        // 计算总页数
        totalPages() {
            return Math.ceil(this.books.length / this.pageSize);
        },
        
        // 当前页的数据
        paginatedBooks() {
            const start = (this.currentPage - 1) * this.pageSize;
            const end = start + this.pageSize;
            return this.books.slice(start, end);
        },
        
        // 分页信息
        pageInfo() {
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.books.length);
            return `显示 ${start}-${end} 条，共 ${this.books.length} 条`;
        }
    },
    
    methods: {
        /**
         * 检查后端是否在线
         */
        async checkBackendHealth() {
            try {
                const response = await axios.get(`${API_BASE_URL}/health`, { 
                    timeout: 3000 
                });
                
                if (response.data.status === 'healthy') {
                    // 后端恢复在线（只在状态变化时更新）
                    if (!this.backendOnline) {
                        console.log('✅ 后端服务已恢复');
                        this.backendOnline = true;
                        this.error = '';
                    }
                    return true;
                }
            } catch (err) {
                // 后端离线（只在状态变化时更新）
                if (this.backendOnline) {
                    console.warn('⚠️ 后端服务已断开');
                    this.backendOnline = false;
                    
                    // 清空所有数据，恢复到初始状态
                    this.books = [];
                    this.searched = false;
                    this.currentKeyword = '';
                    this.dataSource = '';
                    this.currentPage = 1;
                    this.loading = false;
                    
                    // 显示断开提示
                    this.error = '后端服务已断开连接，请重新启动后端程序';
                    
                    console.log('🔄 已清空所有数据，恢复到初始状态');
                }
                return false;
            }
        },
        
        /**
         * 启动心跳检测
         */
        startHeartbeat() {
            // 清除旧的定时器
            if (this.heartbeatTimer) {
                clearInterval(this.heartbeatTimer);
            }
            
            // 每5秒检测一次
            this.heartbeatTimer = setInterval(() => {
                this.checkBackendHealth();
            }, 5000);
            
            console.log('💓 心跳检测已启动');
        },
        
        /**
         * 停止心跳检测
         */
        stopHeartbeat() {
            if (this.heartbeatTimer) {
                clearInterval(this.heartbeatTimer);
                this.heartbeatTimer = null;
                console.log('💔 心跳检测已停止');
            }
        },
        
        /**
         * 爬取图书（从网站爬取并保存到数据库）
         */
        async crawl() {
            // 检查后端是否在线
            if (!this.backendOnline) {
                this.error = '后端服务未运行，请先启动后端程序';
                return;
            }
            
            // 验证输入
            if (!this.keyword.trim()) {
                this.error = '请输入搜索关键词';
                return;
            }
            
            // 验证数量
            let maxBooks = parseInt(this.maxBooks);
            
            // 允许 0（表示爬取所有）
            if (isNaN(maxBooks) || maxBooks < 0) {
                maxBooks = 20;
                this.maxBooks = 20;
            } else if (maxBooks > 500) {
                maxBooks = 500;
                this.maxBooks = 500;
            }
            
            // 显示提示
            if (maxBooks === 0) {
                if (!confirm('您选择了爬取所有数据，这可能需要较长时间。是否继续？')) {
                    return;
                }
            }
            
            // 重置状态
            this.loading = true;
            this.error = '';
            this.books = [];
            this.searched = false;
            this.dataSource = '';
            
            const startTime = Date.now();
            console.log(`[${new Date().toLocaleTimeString()}] 开始爬取，关键词: ${this.keyword.trim()}, 数量: ${maxBooks}`);
            
            try {
                // 调用后端爬取 API
                const response = await axios.post(`${API_BASE_URL}/api/crawl`, {
                    keyword: this.keyword.trim(),
                    max_books: maxBooks,
                    proxy: this.proxy.trim() || null
                }, {
                    timeout: 180000  // 3分钟超时
                });
                
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                console.log(`[${new Date().toLocaleTimeString()}] 爬取完成，耗时: ${elapsed}秒，响应:`, response.data);
                
                // 处理响应
                if (response.data && response.data.success) {
                    const crawlData = response.data;
                    
                    // 显示爬取统计信息
                    console.log(`📊 爬取统计:`);
                    console.log(`   爬取数量: ${crawlData.total_crawled}`);
                    console.log(`   保存数量: ${crawlData.total_saved}`);
                    console.log(`   去重数量: ${crawlData.total_duplicates}`);
                    console.log(`   去重关键词: ${crawlData.dedup_key}`);
                    
                    // 爬取完成后，从数据库获取该关键词的所有数据
                    console.log(`🔄 正在从数据库获取所有相关数据...`);
                    
                    try {
                        const dbResponse = await axios.get(`${API_BASE_URL}/api/books?keyword=${encodeURIComponent(this.keyword.trim())}`);
                        
                        if (dbResponse.data.success) {
                            this.books = dbResponse.data.books;
                            this.currentKeyword = this.keyword.trim();
                            this.searched = true;
                            this.dataSource = `爬取并保存 (爬取${crawlData.total_crawled}本, 新增${crawlData.total_saved}本, 去重${crawlData.total_duplicates}本)`;
                            this.currentPage = 1;
                            
                            if (this.books.length === 0) {
                                this.error = '没有找到相关图书，请尝试其他关键词';
                            } else {
                                console.log(`✅ 从数据库获取到 ${this.books.length} 本图书`);
                            }
                        }
                    } catch (dbErr) {
                        console.error('从数据库获取数据失败:', dbErr);
                        // 如果数据库查询失败，使用爬取的数据
                        this.books = crawlData.books || [];
                        this.currentKeyword = crawlData.keyword || this.keyword.trim();
                        this.searched = true;
                        this.dataSource = `爬取 (爬取${crawlData.total_crawled}本, 新增${crawlData.total_saved}本, 去重${crawlData.total_duplicates}本)`;
                        this.currentPage = 1;
                    }
                } else {
                    this.error = '爬取失败，请重试';
                    console.error('响应格式错误:', response.data);
                }
                
            } catch (err) {
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                console.error(`[${new Date().toLocaleTimeString()}] 爬取错误，耗时: ${elapsed}秒，错误:`, err);
                
                // 检查是否是后端断开
                if (err.code === 'ERR_NETWORK' || err.message.includes('Network Error')) {
                    // 立即检查后端状态
                    const isOnline = await this.checkBackendHealth();
                    if (!isOnline) {
                        this.error = '后端服务已断开连接，爬取已中断';
                        // 清空数据
                        this.books = [];
                        this.searched = false;
                        this.currentKeyword = '';
                        this.dataSource = '';
                        this.currentPage = 1;
                        return;
                    }
                }
                
                // 错误处理
                if (err.code === 'ECONNABORTED') {
                    this.error = '爬取超时（超过3分钟），请减少爬取数量或稍后重试';
                } else if (err.response) {
                    this.error = `爬取失败: ${err.response.data.detail || err.response.statusText}`;
                } else if (err.request) {
                    this.error = '无法连接到服务器，后端可能已退出';
                    this.backendOnline = false;
                } else {
                    this.error = `爬取失败: ${err.message}`;
                }
                
            } finally {
                // 确保恢复界面状态
                this.loading = false;
                const totalElapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                console.log(`[${new Date().toLocaleTimeString()}] 爬取流程结束，总耗时: ${totalElapsed}秒，界面已恢复`);
            }
        },
        
        /**
         * 展示数据库中的图书
         */
        async showBooks() {
            // 检查后端是否在线
            if (!this.backendOnline) {
                this.error = '后端服务未运行，请先启动后端程序';
                return;
            }
            
            // 重置状态
            this.loading = true;
            this.error = '';
            this.books = [];
            this.searched = false;
            this.dataSource = '';
            
            try {
                // 构建请求 URL
                let url = `${API_BASE_URL}/api/books`;
                if (this.keyword.trim()) {
                    url += `?keyword=${encodeURIComponent(this.keyword.trim())}`;
                }
                
                // 调用后端展示 API
                const response = await axios.get(url);
                
                // 处理响应
                if (response.data.success) {
                    this.books = response.data.books;
                    this.currentKeyword = response.data.keyword;
                    this.searched = true;
                    this.dataSource = '数据库';
                    this.currentPage = 1; // 重置到第一页
                    
                    if (this.books.length === 0) {
                        this.error = this.keyword.trim() 
                            ? '数据库中没有该关键词的图书，请先爬取数据' 
                            : '数据库中暂无数据，请先爬取图书';
                    }
                } else {
                    this.error = '获取数据失败，请重试';
                }
                
            } catch (err) {
                // 错误处理
                console.error('获取数据错误：', err);
                
                // 检查是否是后端断开
                if (err.code === 'ERR_NETWORK' || err.message.includes('Network Error')) {
                    const isOnline = await this.checkBackendHealth();
                    if (!isOnline) {
                        this.error = '后端服务已断开连接';
                        // 清空数据
                        this.books = [];
                        this.searched = false;
                        this.currentKeyword = '';
                        this.dataSource = '';
                        this.currentPage = 1;
                        return;
                    }
                }
                
                if (err.response) {
                    this.error = `获取数据失败: ${err.response.data.detail || err.response.statusText}`;
                } else if (err.request) {
                    this.error = '无法连接到服务器，后端可能已退出';
                    this.backendOnline = false;
                } else {
                    this.error = `获取数据失败: ${err.message}`;
                }
                
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 处理图片加载错误
         */
        handleImageError(event) {
            event.target.src = 'https://via.placeholder.com/350x300?text=暂无封面';
        },
        
        /**
         * 清空搜索
         */
        clearSearch() {
            this.keyword = '';
            this.books = [];
            this.error = '';
            this.searched = false;
            this.currentKeyword = '';
            this.dataSource = '';
            this.currentPage = 1;
        },
        
        /**
         * 上一页
         */
        prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
            }
        },
        
        /**
         * 下一页
         */
        nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
            }
        },
        
        /**
         * 跳转到指定页
         */
        goToPage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
            }
        }
    },
    
    mounted() {
        console.log('当当网图书爬虫应用已加载');
        
        // 检测后端端口
        detectBackendPort().then(port => {
            console.log('API 地址:', API_BASE_URL);
            if (port !== 8001) {
                console.warn(`注意：后端运行在端口 ${port}，而不是默认的 8001`);
            }
            
            // 启动心跳检测
            this.startHeartbeat();
        });
    },
    
    beforeUnmount() {
        // 组件销毁前停止心跳检测
        this.stopHeartbeat();
    }
}).mount('#app');
