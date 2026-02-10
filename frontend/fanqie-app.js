/**
 * 番茄小说爬虫应用
 * 使用 Vue 3
 */

const { createApp } = Vue;

// API 基础地址
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
            currentTab: 'recommend',  // 当前标签页：recommend, detail, author
            loading: false,           // 加载状态
            
            // 推荐列表
            recommendBooks: [],
            
            // 书籍详情
            bookName: '',
            bookDetail: null,
            
            // 作者搜索
            authorName: '',
            currentAuthor: '',
            authorBooks: []
        }
    },
    
    computed: {
        hasData() {
            if (this.currentTab === 'recommend') {
                return this.recommendBooks.length > 0;
            } else if (this.currentTab === 'detail') {
                return this.bookDetail !== null;
            } else if (this.currentTab === 'author') {
                return this.authorBooks.length > 0;
            }
            return false;
        }
    },
    
    methods: {
        /**
         * 返回首页
         */
        goBack() {
            window.location.href = 'home.html';
        },
        
        /**
         * 爬取推荐列表
         */
        async crawlRecommend() {
            this.loading = true;
            this.recommendBooks = [];
            
            try {
                console.log('开始爬取推荐列表');
                
                const response = await axios.post(`${API_BASE_URL}/api/crawl/fanqie/recommend`, {}, {
                    timeout: 90000
                });
                
                console.log('爬取响应:', response.data);
                
                if (response.data.success) {
                    this.recommendBooks = response.data.books || [];
                    
                    if (this.recommendBooks.length === 0) {
                        alert('未找到推荐书籍');
                    } else {
                        alert(`爬取完成！共获取 ${this.recommendBooks.length} 本推荐书籍`);
                    }
                } else {
                    alert('爬取失败，请重试');
                }
            } catch (error) {
                console.error('爬取错误:', error);
                if (error.response) {
                    alert(`爬取失败: ${error.response.data.detail || error.message}`);
                } else if (error.request) {
                    alert('无法连接到后端服务，请确保后端已启动');
                } else {
                    alert(`爬取失败: ${error.message}`);
                }
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 展示数据库推荐
         */
        async showRecommend() {
            this.loading = true;
            this.recommendBooks = [];
            
            try {
                console.log('获取数据库推荐');
                
                const response = await axios.get(`${API_BASE_URL}/api/fanqie/recommend`, {
                    params: { limit: 100 }
                });
                
                console.log('数据库响应:', response.data);
                
                if (response.data.success) {
                    this.recommendBooks = response.data.books || [];
                    
                    if (this.recommendBooks.length === 0) {
                        alert('数据库中暂无推荐数据');
                    }
                } else {
                    alert('获取数据失败，请重试');
                }
            } catch (error) {
                console.error('获取数据错误:', error);
                if (error.response) {
                    alert(`获取数据失败: ${error.response.data.detail || error.message}`);
                } else {
                    alert(`获取数据失败: ${error.message}`);
                }
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 爬取书籍详情
         */
        async crawlDetail() {
            if (!this.bookName.trim()) {
                alert('请输入书名');
                return;
            }
            
            this.loading = true;
            this.bookDetail = null;
            
            try {
                console.log(`开始爬取书籍详情: ${this.bookName}`);
                
                const response = await axios.post(`${API_BASE_URL}/api/crawl/fanqie/detail`, null, {
                    params: {
                        book_name: this.bookName
                    },
                    timeout: 90000
                });
                
                console.log('爬取响应:', response.data);
                
                if (response.data.success) {
                    this.bookDetail = response.data.book;
                    alert('爬取成功！');
                } else {
                    alert('未找到书籍');
                }
            } catch (error) {
                console.error('爬取错误:', error);
                if (error.response) {
                    alert(`爬取失败: ${error.response.data.detail || error.message}`);
                } else {
                    alert(`爬取失败: ${error.message}`);
                }
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 查看详情（通过书籍ID）
         */
        async viewDetail(bookId) {
            this.currentTab = 'detail';
            this.loading = true;
            this.bookDetail = null;
            
            try {
                console.log(`查看书籍详情: ${bookId}`);
                
                // 先尝试从数据库获取
                try {
                    const dbResponse = await axios.get(`${API_BASE_URL}/api/fanqie/detail/${bookId}`);
                    if (dbResponse.data.success) {
                        this.bookDetail = dbResponse.data.book;
                        this.loading = false;
                        return;
                    }
                } catch (e) {
                    console.log('数据库中未找到，开始爬取');
                }
                
                // 数据库中没有，开始爬取
                const response = await axios.post(`${API_BASE_URL}/api/crawl/fanqie/detail`, null, {
                    params: {
                        book_id: bookId
                    },
                    timeout: 90000
                });
                
                if (response.data.success) {
                    this.bookDetail = response.data.book;
                } else {
                    alert('未找到书籍详情');
                }
            } catch (error) {
                console.error('获取详情错误:', error);
                alert(`获取详情失败: ${error.message}`);
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 搜索作者
         */
        async searchAuthor(authorName) {
            this.currentTab = 'author';
            this.authorName = authorName || this.authorName;
            await this.crawlAuthor();
        },
        
        /**
         * 爬取作者书籍
         */
        async crawlAuthor() {
            if (!this.authorName.trim()) {
                alert('请输入作者名');
                return;
            }
            
            this.loading = true;
            this.authorBooks = [];
            this.currentAuthor = this.authorName;
            
            try {
                console.log(`开始搜索作者: ${this.authorName}`);
                
                const response = await axios.post(`${API_BASE_URL}/api/crawl/fanqie/author`, null, {
                    params: {
                        author_name: this.authorName
                    },
                    timeout: 90000
                });
                
                console.log('搜索响应:', response.data);
                
                if (response.data.success) {
                    this.authorBooks = response.data.books || [];
                    
                    if (this.authorBooks.length === 0) {
                        alert(`未找到作者"${this.authorName}"的作品`);
                    } else {
                        alert(`找到 ${this.authorBooks.length} 本作品`);
                    }
                } else {
                    alert('搜索失败，请重试');
                }
            } catch (error) {
                console.error('搜索错误:', error);
                if (error.response) {
                    alert(`搜索失败: ${error.response.data.detail || error.message}`);
                } else {
                    alert(`搜索失败: ${error.message}`);
                }
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 展示数据库中的作者书籍
         */
        async showAuthorBooks() {
            if (!this.authorName.trim()) {
                alert('请输入作者名');
                return;
            }
            
            this.loading = true;
            this.authorBooks = [];
            this.currentAuthor = this.authorName;
            
            try {
                console.log(`获取数据库中的作者书籍: ${this.authorName}`);
                
                const response = await axios.get(`${API_BASE_URL}/api/fanqie/author/${this.authorName}`);
                
                console.log('数据库响应:', response.data);
                
                if (response.data.success) {
                    this.authorBooks = response.data.books || [];
                    
                    if (this.authorBooks.length === 0) {
                        alert(`数据库中暂无作者"${this.authorName}"的作品`);
                    }
                } else {
                    alert('获取数据失败，请重试');
                }
            } catch (error) {
                console.error('获取数据错误:', error);
                if (error.response) {
                    alert(`获取数据失败: ${error.response.data.detail || error.message}`);
                } else {
                    alert(`获取数据失败: ${error.message}`);
                }
            } finally {
                this.loading = false;
            }
        },
        
        /**
         * 处理图片加载错误
         */
        handleImageError(event) {
            event.target.style.display = 'none';
            event.target.parentElement.innerHTML = '<div class="no-cover">📚</div>';
        }
    },
    
    async mounted() {
        console.log('番茄小说爬虫页面已加载');
        
        // 检测后端端口
        await detectBackendPort();
    }
}).mount('#app');
