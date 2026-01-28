"""
FastAPI 后端 API
提供图书搜索接口
"""

# 标准库导入
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

# 检查并导入第三方库
try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as e:
    print("="*60)
    print("❌ 缺少必要的依赖包！")
    print("="*60)
    print(f"错误信息: {e}")
    print()
    print("请运行以下命令安装依赖：")
    print("pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn[standard] pydantic")
    print()
    print("或者运行：")
    print("pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt")
    print("="*60)
    sys.exit(1)

# 添加父目录到路径，以便导入 dangdang 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def find_available_port(start_port=8000, max_attempts=10):
    """查找可用端口"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    return None

# 导入爬虫模块
try:
    from dangdang import run_spider, DangDangSpider
    from db_config import MYSQL_CONFIG, USE_MYSQL
    from mysql_pool import MySQLPool
except ImportError as e:
    print("="*60)
    print("❌ 导入 dangdang 模块失败！")
    print("="*60)
    print(f"错误信息: {e}")
    print(f"当前路径: {os.getcwd()}")
    print(f"父目录: {parent_dir}")
    print()
    print("请确保 dangdang.py 文件存在于项目根目录")
    print("="*60)
    sys.exit(1)


app = FastAPI(
    title="当当网图书爬虫 API",
    description="提供图书搜索和数据爬取功能",
    version="1.0.0"
)

# 初始化 MySQL 连接池（如果启用）
if USE_MYSQL:
    try:
        MySQLPool.initialize(
            host=MYSQL_CONFIG.get('host', 'localhost'),
            port=MYSQL_CONFIG.get('port', 3306),
            user=MYSQL_CONFIG.get('user', 'root'),
            password=MYSQL_CONFIG.get('password', ''),
            database=MYSQL_CONFIG.get('database', 'dangdang_books'),
            mincached=2,
            maxcached=10,
            maxconnections=20
        )
    except Exception as e:
        print(f"⚠️ MySQL 连接池初始化失败: {e}")
        print("⚠️ 将禁用数据库存储功能")
        USE_MYSQL = False

# 配置 CORS - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """搜索请求模型"""
    keyword: str = Field(..., min_length=1, max_length=50, description="搜索关键词")
    max_books: int = Field(default=20, ge=0, le=500, description="最大爬取数量（0表示爬取所有）")
    proxy: Optional[str] = Field(default=None, description="代理地址（格式：http://ip:port）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "keyword": "Python",
                "max_books": 20,
                "proxy": None
            }
        }
    }


class BookInfo(BaseModel):
    """图书信息模型"""
    标题: str = ""
    作者: str = ""
    出版社: str = ""
    出版时间: str = ""
    原价: str = ""
    现价: str = ""
    ISBN: str = ""
    评分: str = ""
    评论数: str = ""
    简介: str = ""
    封面图: str = ""
    详情页URL: str = ""


class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool
    keyword: str
    count: int
    books: List[Dict]
    total_crawled: int = 0  # 爬取总数
    total_saved: int = 0  # 保存总数
    total_duplicates: int = 0  # 去重总数
    dedup_key: str = ""  # 去重关键词
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "keyword": "Python",
                "count": 2,
                "total_crawled": 20,
                "total_saved": 18,
                "total_duplicates": 2,
                "dedup_key": "标题 + 作者",
                "books": [
                    {
                        "标题": "Python编程从入门到实践",
                        "作者": "埃里克·马瑟斯",
                        "出版社": "人民邮电出版社",
                        "现价": "¥89.00"
                    }
                ]
            }
        }
    }


# 线程池执行器，用于异步执行爬虫任务
executor = ThreadPoolExecutor(max_workers=3)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "当当网图书爬虫 API",
        "version": "1.0.0",
        "endpoints": {
            "crawl": "/api/crawl",
            "books": "/api/books",
            "stats": "/api/stats",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/crawl", response_model=SearchResponse)
async def crawl_books(request: SearchRequest):
    """
    爬取图书 API（爬取并保存到数据库）
    
    参数:
        request: 包含搜索关键词和爬取数量的请求体
    
    返回:
        包含图书列表的响应
    """
    keyword = request.keyword.strip()
    max_books = request.max_books
    proxy = request.proxy.strip() if request.proxy else None
    
    if not keyword:
        raise HTTPException(status_code=400, detail="关键词不能为空")
    
    if len(keyword) > 50:
        raise HTTPException(status_code=400, detail="关键词过长，请输入50字以内")
    
    if max_books < 0 or max_books > 500:
        raise HTTPException(status_code=400, detail="爬取数量必须在 0-500 之间（0表示爬取所有）")
    
    if max_books == 0:
        print(f"\n{'='*60}")
        print(f"📥 收到爬取请求: 关键词='{keyword}', 模式=无限制（爬取所有）")
        if proxy:
            print(f"🔒 代理设置: {proxy}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print(f"📥 收到爬取请求: 关键词='{keyword}', 数量={max_books}")
        if proxy:
            print(f"🔒 代理设置: {proxy}")
        print(f"{'='*60}\n")
    
    try:
        # 在线程池中异步运行爬虫，避免阻塞主线程
        loop = asyncio.get_event_loop()
        
        print("🔄 开始执行爬虫任务...")
        
        # 使用 asyncio.wait_for 添加超时保护
        try:
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    executor,
                    lambda: run_spider(
                        keyword=keyword,
                        thread_count=3,
                        use_mysql=USE_MYSQL,
                        mysql_config=MYSQL_CONFIG,
                        max_books=max_books,
                        proxy=proxy
                    )
                ),
                timeout=180.0  # 3分钟超时（作为最后的保护）
            )
        except asyncio.TimeoutError:
            print("⚠️ 爬虫任务超时，强制返回")
            # 超时后返回空结果
            results = []
        
        print(f"🔄 爬虫任务执行完毕，返回 {len(results) if results else 0} 条结果")
        
        # 确保 results 不为 None
        if results is None:
            results = {
                'books': [],
                'total_crawled': 0,
                'total_saved': 0,
                'total_duplicates': 0,
                'dedup_key': '标题 + 作者'
            }
        
        books = results.get('books', [])
        
        print(f"\n{'='*60}")
        print(f"✅ 爬取请求完成:")
        print(f"   爬取数量: {results.get('total_crawled', 0)} 本")
        print(f"   保存数量: {results.get('total_saved', 0)} 本")
        print(f"   去重数量: {results.get('total_duplicates', 0)} 本")
        print(f"   去重关键词: {results.get('dedup_key', '标题 + 作者')}")
        print(f"{'='*60}\n")
        
        response_data = SearchResponse(
            success=True,
            keyword=keyword,
            count=len(books),
            books=books,
            total_crawled=results.get('total_crawled', 0),
            total_saved=results.get('total_saved', 0),
            total_duplicates=results.get('total_duplicates', 0),
            dedup_key=results.get('dedup_key', '标题 + 作者')
        )
        
        print(f"📤 准备返回响应: success={response_data.success}, count={response_data.count}, saved={response_data.total_saved}")
        return response_data
    
    except asyncio.TimeoutError:
        print(f"\n{'='*60}")
        print(f"⚠️ 请求超时")
        print(f"{'='*60}\n")
        raise HTTPException(
            status_code=504,
            detail="爬取超时，请减少爬取数量或稍后重试"
        )
    
    except Exception as e:
        # 记录错误日志
        print(f"\n{'='*60}")
        print(f"❌ 爬取错误: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        raise HTTPException(
            status_code=500,
            detail=f"爬取失败: {str(e)}"
        )


@app.get("/api/books", response_model=SearchResponse)
async def get_books_from_db(keyword: Optional[str] = None, limit: int = 100):
    """
    从数据库获取图书数据
    
    参数:
        keyword: 搜索关键词（可选）
        limit: 返回数量限制
    
    返回:
        包含图书列表的响应
    """
    try:
        # 根据关键词获取数据
        if keyword:
            books = MySQLPool.get_books_by_keyword(keyword.strip())
        else:
            books = MySQLPool.get_all_books(limit=limit)
        
        return SearchResponse(
            success=True,
            keyword=keyword or "全部",
            count=len(books),
            books=books
        )
    
    except Exception as e:
        print(f"数据库查询错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"数据库查询失败: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    try:
        stats = MySQLPool.get_statistics()
        
        return {
            "success": True,
            "total_books": stats.get('total_books', 0),
            "keywords": stats.get('keywords', []),
            "status": "running"
        }
    except Exception as e:
        return {
            "success": False,
            "total_books": 0,
            "keywords": [],
            "status": "running",
            "error": str(e)
        }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    print(f"全局异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "detail": f"服务器错误: {str(exc)}"
        }
    )


def cleanup():
    """清理资源"""
    print("\n🧹 正在清理资源...")
    
    # 关闭线程池
    try:
        executor.shutdown(wait=False, cancel_futures=True)
        print("✅ 线程池已关闭")
    except Exception as e:
        print(f"⚠️ 关闭线程池失败: {e}")
    
    # 关闭数据库连接池
    if USE_MYSQL:
        try:
            if MySQLPool._pool:
                MySQLPool._pool.close()
                print("✅ 数据库连接池已关闭")
        except Exception as e:
            print(f"⚠️ 关闭数据库连接池失败: {e}")


if __name__ == "__main__":
    import signal
    import atexit
    
    # 注册退出时的清理函数
    atexit.register(cleanup)
    
    # 注册信号处理器
    def signal_handler(sig, frame):
        print("\n")
        print("="*60)
        print("🛑 收到中断信号，正在停止服务器...")
        print("="*60)
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 查找可用端口
    port = find_available_port(8001, 10)
    
    if port is None:
        print("="*60)
        print("❌ 错误：无法找到可用端口（8000-8009 都被占用）")
        print("="*60)
        print("请关闭占用端口的程序")
        print("="*60)
        sys.exit(1)
    
    print("="*60)
    print("🚀 当当网图书爬虫 API 启动中...")
    print("="*60)
    print(f"📍 API 地址: http://127.0.0.1:{port}")
    print(f"📍 API 文档: http://127.0.0.1:{port}/docs")
    print(f"📍 健康检查: http://127.0.0.1:{port}/health")
    print(f"📍 爬取接口: http://127.0.0.1:{port}/api/crawl")
    print(f"📍 展示接口: http://127.0.0.1:{port}/api/books")
    print(f"📍 统计接口: http://127.0.0.1:{port}/api/stats")
    
    if port != 8000:
        print(f"⚠️  注意：端口 8000 被占用，使用端口 {port}")
        print(f"⚠️  请修改前端 app.js 中的 API_BASE_URL 为: http://127.0.0.1:{port}")
    
    print("="*60)
    print("按 Ctrl+C 停止服务器")
    print("="*60)
    print()
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n")
        print("="*60)
        print("✅ 服务器已停止")
        print("="*60)
    except Exception as e:
        print("\n")
        print("="*60)
        print(f"❌ 服务器启动失败: {e}")
        print("="*60)
        sys.exit(1)
    finally:
        cleanup()
