"""
番茄小说爬虫 - 使用feapder框架
功能：
1. 爬取推荐书籍列表（书名+ID）
2. 根据书名/ID爬取书籍详情
3. 根据作者名搜索作者的所有书籍
"""

import feapder
from feapder import Request
from typing import List, Dict, Optional
from mysql_pool import MySQLPool
import re
from bs4 import BeautifulSoup


class FanQieRecommendSpider(feapder.AirSpider):
    """番茄小说推荐列表爬虫 - 只爬取书名和ID"""
    
    # 自定义配置
    __custom_setting__ = dict(
        SPIDER_THREAD_COUNT=3,
        SPIDER_MAX_RETRY_TIMES=2,
        REQUEST_TIMEOUT=30,
        RETRY_FAILED_REQUESTS=False,
        LOG_LEVEL="ERROR",
    )
    
    def __init__(self, use_mysql=True, max_books=50, proxy=None, *args, **kwargs):
        """
        初始化爬虫
        :param use_mysql: 是否使用 MySQL 存储
        :param max_books: 最大爬取数量
        :param proxy: 代理地址
        """
        super().__init__(*args, **kwargs)
        self.results = []
        self.use_mysql = use_mysql
        self.max_books = max_books
        self.proxy = proxy
        self.crawled_count = 0
    
    def start_requests(self):
        """生成初始请求 - 推荐页面"""
        # 番茄小说推荐页面URL
        recommend_url = "https://fanqienovel.com/page/recommend"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        request_kwargs = {
            "url": recommend_url,
            "headers": headers,
            "callback": self.parse_recommend_page
        }
        
        if self.proxy:
            request_kwargs["proxies"] = {
                "http": self.proxy,
                "https": self.proxy
            }
        
        yield Request(**request_kwargs)
    
    def parse_recommend_page(self, request, response):
        """解析推荐页面 - 只提取书名和ID（使用 BeautifulSoup）"""
        try:
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取书籍列表
            book_items = soup.select('.book-item')
            
            if not book_items:
                book_items = soup.select('[class*="recommend-item"]')
            
            for item in book_items:
                if self.crawled_count >= self.max_books:
                    return
                
                # 提取书名
                title_tag = item.select_one('h3')
                if not title_tag:
                    title_tag = item.select_one('.title')
                title = title_tag.get_text(strip=True) if title_tag else None
                
                # 提取书籍ID（从URL中提取）
                link_tag = item.select_one('a')
                detail_url = link_tag.get('href') if link_tag else None
                book_id = None
                if detail_url:
                    # 从URL中提取ID，例如：/page/123456
                    match = re.search(r'/page/(\d+)', detail_url)
                    if match:
                        book_id = match.group(1)
                
                if title and book_id:
                    book_data = {
                        "书名": title,
                        "书籍ID": book_id,
                        "详情页URL": response.urljoin(detail_url) if detail_url else ""
                    }
                    
                    self.results.append(book_data)
                    self.crawled_count += 1
                    
                    # 保存到数据库
                    if self.use_mysql:
                        try:
                            MySQLPool.save_fanqie_recommend(book_data)
                        except Exception as e:
                            pass
        
        except Exception as e:
            pass


class FanQieDetailSpider(feapder.AirSpider):
    """番茄小说详情爬虫 - 根据书名或ID爬取完整详情"""
    
    # 自定义配置
    __custom_setting__ = dict(
        SPIDER_THREAD_COUNT=3,
        SPIDER_MAX_RETRY_TIMES=2,
        REQUEST_TIMEOUT=30,
        RETRY_FAILED_REQUESTS=False,
        LOG_LEVEL="ERROR",
    )
    
    def __init__(self, book_name=None, book_id=None, use_mysql=True, proxy=None, *args, **kwargs):
        """
        初始化爬虫
        :param book_name: 书名
        :param book_id: 书籍ID
        :param use_mysql: 是否使用 MySQL 存储
        :param proxy: 代理地址
        """
        super().__init__(*args, **kwargs)
        self.book_name = book_name
        self.book_id = book_id
        self.results = []
        self.use_mysql = use_mysql
        self.proxy = proxy
    
    def start_requests(self):
        """生成初始请求 - 详情页"""
        if self.book_id:
            # 使用书籍ID构造URL
            detail_url = f"https://fanqienovel.com/page/{self.book_id}"
        elif self.book_name:
            # 使用书名搜索
            detail_url = f"https://fanqienovel.com/search/{self.book_name}"
        else:
            return
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        request_kwargs = {
            "url": detail_url,
            "headers": headers,
            "callback": self.parse_detail_page if self.book_id else self.parse_search_page
        }
        
        if self.proxy:
            request_kwargs["proxies"] = {
                "http": self.proxy,
                "https": self.proxy
            }
        
        yield Request(**request_kwargs)
    
    def parse_search_page(self, request, response):
        """解析搜索页面，找到第一个匹配的书籍（使用 BeautifulSoup）"""
        try:
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到第一个匹配的书籍
            first_book = soup.select_one('.book-item a')
            
            if first_book:
                detail_url = first_book.get('href')
                if detail_url:
                    detail_url = response.urljoin(detail_url)
                    
                    request_kwargs = {
                        "url": detail_url,
                        "headers": request.headers,
                        "callback": self.parse_detail_page
                    }
                    
                    if self.proxy:
                        request_kwargs["proxies"] = {
                            "http": self.proxy,
                            "https": self.proxy
                        }
                    
                    yield Request(**request_kwargs)
        except Exception as e:
            pass
    
    def parse_detail_page(self, request, response):
        """解析详情页 - 提取完整信息（使用 BeautifulSoup）"""
        try:
            # 提取书籍ID
            book_id = None
            match = re.search(r'/page/(\d+)', response.url)
            if match:
                book_id = match.group(1)
            
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取详细信息
            # 书名
            title_tag = soup.select_one('.info-name h1')
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title:
                title_tag = soup.select_one('.book-title')
                title = title_tag.get_text(strip=True) if title_tag else None
            
            # 作者
            author_tag = soup.select_one('.author-name-text')
            author = author_tag.get_text(strip=True) if author_tag else None
            if not author:
                author_tag = soup.select_one('.author')
                author = author_tag.get_text(strip=True) if author_tag else None
            
            # 分类
            category_tag = soup.select_one('.category')
            category = category_tag.get_text(strip=True) if category_tag else None
            if not category:
                category_tag = soup.select_one('.tag')
                category = category_tag.get_text(strip=True) if category_tag else None
            
            # 状态
            status_tag = soup.select_one('.status')
            status = status_tag.get_text(strip=True) if status_tag else None
            if not status:
                status_tag = soup.select_one('.book-status')
                status = status_tag.get_text(strip=True) if status_tag else None
            
            # 简介
            desc_tag = soup.select_one('.page-abstract-content')
            description = desc_tag.get_text(strip=True) if desc_tag else None
            if not description:
                desc_tag = soup.select_one('.book-intro')
                description = desc_tag.get_text(strip=True) if desc_tag else None
            
            # 字数
            word_count = None
            word_tags = soup.find_all('span', string=re.compile('字数'))
            if word_tags:
                word_parent = word_tags[0].parent
                word_count_tag = word_parent.find_next_sibling('span')
                word_count = word_count_tag.get_text(strip=True) if word_count_tag else None
            
            # 章节数
            chapter_count = None
            chapter_tags = soup.find_all('span', string=re.compile('章节'))
            if chapter_tags:
                chapter_parent = chapter_tags[0].parent
                chapter_count_tag = chapter_parent.find_next_sibling('span')
                chapter_count = chapter_count_tag.get_text(strip=True) if chapter_count_tag else None
            
            # 封面图
            cover_tag = soup.select_one('img.book-cover')
            cover_image = cover_tag.get('src') if cover_tag else None
            if not cover_image:
                cover_tag = soup.select_one('.cover img')
                cover_image = cover_tag.get('src') if cover_tag else None
            
            # 最新章节
            latest_tag = soup.select_one('.latest-chapter a')
            latest_chapter = latest_tag.get_text(strip=True) if latest_tag else None
            
            # 更新时间
            update_tag = soup.select_one('.update-time')
            update_time = update_tag.get_text(strip=True) if update_tag else None
            
            # 构造书籍数据
            book_data = {
                "书籍ID": book_id if book_id else "",
                "标题": title.strip() if title else "",
                "作者": author.strip() if author else "",
                "分类": category.strip() if category else "",
                "状态": status.strip() if status else "",
                "简介": description.strip() if description else "",
                "字数": word_count.strip() if word_count else "",
                "章节数": chapter_count.strip() if chapter_count else "",
                "封面图": cover_image.strip() if cover_image else "",
                "最新章节": latest_chapter.strip() if latest_chapter else "",
                "更新时间": update_time.strip() if update_time else "",
                "详情页URL": response.url
            }
            
            self.results.append(book_data)
            
            # 保存到数据库
            if self.use_mysql:
                try:
                    result = MySQLPool.save_fanqie_book_detail(book_data)
                    if result['success'] and book_data['作者']:
                        # 同时保存作者信息
                        MySQLPool.save_fanqie_author(book_data['作者'], book_data['书籍ID'])
                except Exception as e:
                    pass
        
        except Exception as e:
            pass


class FanQieAuthorSpider(feapder.AirSpider):
    """番茄小说作者爬虫 - 根据作者名搜索该作者的所有书籍"""
    
    # 自定义配置
    __custom_setting__ = dict(
        SPIDER_THREAD_COUNT=3,
        SPIDER_MAX_RETRY_TIMES=2,
        REQUEST_TIMEOUT=30,
        RETRY_FAILED_REQUESTS=False,
        LOG_LEVEL="ERROR",
    )
    
    def __init__(self, author_name="", use_mysql=True, max_books=50, proxy=None, *args, **kwargs):
        """
        初始化爬虫
        :param author_name: 作者名
        :param use_mysql: 是否使用 MySQL 存储
        :param max_books: 最大爬取数量
        :param proxy: 代理地址
        """
        super().__init__(*args, **kwargs)
        self.author_name = author_name
        self.results = []
        self.use_mysql = use_mysql
        self.max_books = max_books
        self.proxy = proxy
        self.crawled_count = 0
    
    def start_requests(self):
        """生成初始请求 - 搜索作者"""
        search_url = f"https://fanqienovel.com/search/{self.author_name}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        request_kwargs = {
            "url": search_url,
            "headers": headers,
            "callback": self.parse_search_page
        }
        
        if self.proxy:
            request_kwargs["proxies"] = {
                "http": self.proxy,
                "https": self.proxy
            }
        
        yield Request(**request_kwargs)
    
    def parse_search_page(self, request, response):
        """解析搜索页面 - 提取该作者的所有书籍（使用 BeautifulSoup）"""
        try:
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取书籍列表
            book_items = soup.select('.book-item')
            
            for item in book_items:
                if self.crawled_count >= self.max_books:
                    return
                
                # 提取书名
                title_tag = item.select_one('h3')
                if not title_tag:
                    title_tag = item.select_one('.title')
                title = title_tag.get_text(strip=True) if title_tag else None
                
                # 提取作者（验证是否匹配）
                author_tag = item.select_one('.author')
                author = author_tag.get_text(strip=True) if author_tag else None
                
                # 只保存匹配作者的书籍
                if author and self.author_name in author:
                    # 提取书籍ID
                    link_tag = item.select_one('a')
                    detail_url = link_tag.get('href') if link_tag else None
                    book_id = None
                    if detail_url:
                        match = re.search(r'/page/(\d+)', detail_url)
                        if match:
                            book_id = match.group(1)
                    
                    if title and book_id:
                        book_data = {
                            "书名": title,
                            "书籍ID": book_id,
                            "作者": author,
                            "详情页URL": response.urljoin(detail_url) if detail_url else ""
                        }
                        
                        self.results.append(book_data)
                        self.crawled_count += 1
                        
                        # 保存到数据库
                        if self.use_mysql:
                            try:
                                MySQLPool.save_fanqie_author_book(author, book_id, title)
                            except Exception as e:
                                pass
        
        except Exception as e:
            pass


# 运行函数
def run_recommend_spider(use_mysql: bool = True, max_books: int = 50, proxy: Optional[str] = None) -> Dict:
    """
    运行推荐列表爬虫
    :param use_mysql: 是否使用 MySQL 存储
    :param max_books: 最大爬取数量
    :param proxy: 代理地址
    :return: 书籍列表
    """
    import threading
    
    spider = None
    spider_thread = None
    
    try:
        spider = FanQieRecommendSpider(
            use_mysql=use_mysql,
            max_books=max_books,
            proxy=proxy
        )
        
        def run_spider_thread():
            try:
                spider.start()
            except Exception as e:
                pass
        
        spider_thread = threading.Thread(target=run_spider_thread, daemon=False)
        spider_thread.start()
        spider_thread.join(timeout=60)
        
        results = spider.results if spider and spider.results else []
        
        return {
            'books': results,
            'total_crawled': len(results)
        }
    
    except Exception as e:
        return {
            'books': [],
            'total_crawled': 0
        }


def run_detail_spider(book_name: Optional[str] = None, book_id: Optional[str] = None, 
                     use_mysql: bool = True, proxy: Optional[str] = None) -> Dict:
    """
    运行详情爬虫
    :param book_name: 书名
    :param book_id: 书籍ID
    :param use_mysql: 是否使用 MySQL 存储
    :param proxy: 代理地址
    :return: 书籍详情
    """
    import threading
    
    spider = None
    spider_thread = None
    
    try:
        spider = FanQieDetailSpider(
            book_name=book_name,
            book_id=book_id,
            use_mysql=use_mysql,
            proxy=proxy
        )
        
        def run_spider_thread():
            try:
                spider.start()
            except Exception as e:
                pass
        
        spider_thread = threading.Thread(target=run_spider_thread, daemon=False)
        spider_thread.start()
        spider_thread.join(timeout=60)
        
        results = spider.results if spider and spider.results else []
        
        return {
            'book': results[0] if results else None,
            'success': len(results) > 0
        }
    
    except Exception as e:
        return {
            'book': None,
            'success': False
        }


def run_author_spider(author_name: str, use_mysql: bool = True, max_books: int = 50, 
                     proxy: Optional[str] = None) -> Dict:
    """
    运行作者爬虫
    :param author_name: 作者名
    :param use_mysql: 是否使用 MySQL 存储
    :param max_books: 最大爬取数量
    :param proxy: 代理地址
    :return: 作者的书籍列表
    """
    import threading
    
    spider = None
    spider_thread = None
    
    try:
        spider = FanQieAuthorSpider(
            author_name=author_name,
            use_mysql=use_mysql,
            max_books=max_books,
            proxy=proxy
        )
        
        def run_spider_thread():
            try:
                spider.start()
            except Exception as e:
                pass
        
        spider_thread = threading.Thread(target=run_spider_thread, daemon=False)
        spider_thread.start()
        spider_thread.join(timeout=60)
        
        results = spider.results if spider and spider.results else []
        
        return {
            'books': results,
            'total_crawled': len(results),
            'author': author_name
        }
    
    except Exception as e:
        return {
            'books': [],
            'total_crawled': 0,
            'author': author_name
        }


if __name__ == "__main__":
    print("番茄小说爬虫")
    print("1. 爬取推荐列表")
    print("2. 爬取书籍详情")
    print("3. 搜索作者书籍")
    
    choice = input("请选择功能 (1/2/3): ").strip()
    
    if choice == "1":
        results = run_recommend_spider()
        print(f"爬取到 {len(results['books'])} 本推荐书籍")
    elif choice == "2":
        book_name = input("请输入书名: ").strip()
        result = run_detail_spider(book_name=book_name)
        if result['success']:
            print(f"成功获取书籍详情: {result['book']['标题']}")
        else:
            print("未找到书籍")
    elif choice == "3":
        author_name = input("请输入作者名: ").strip()
        results = run_author_spider(author_name)
        print(f"找到 {len(results['books'])} 本 {author_name} 的书籍")
