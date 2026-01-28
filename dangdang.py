"""
当当网图书爬虫 - 使用feapder框架
功能：根据关键词搜索图书，并爬取详情页信息
"""

import feapder
from feapder import Request
from typing import List, Dict, Optional
from mysql_pool import MySQLPool


class DangDangSpider(feapder.AirSpider):
    """当当网图书爬虫"""
    
    # 自定义配置
    __custom_setting__ = dict(
        SPIDER_THREAD_COUNT=3,  # 线程数（减少线程数，提高稳定性）
        SPIDER_MAX_RETRY_TIMES=2,  # 最大重试次数
        REQUEST_TIMEOUT=30,  # 请求超时时间（秒）
        RETRY_FAILED_REQUESTS=False,  # 不重试失败的请求
        LOG_LEVEL="ERROR",  # 只显示错误日志
    )
    
    def __init__(self, keyword="Python", use_mysql=True, max_books=20, proxy=None, *args, **kwargs):
        """
        初始化爬虫
        :param keyword: 搜索关键词
        :param use_mysql: 是否使用 MySQL 存储（默认 True）
        :param max_books: 最大爬取图书数量（默认 20，0表示爬取所有）
        :param proxy: 代理地址（格式：http://ip:port 或 https://ip:port）
        """
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.results = []  # 存储爬取结果
        self.use_mysql = use_mysql
        self.target_new_books = max_books  # 目标新增数量
        self.is_unlimited = (max_books == 0)  # 是否无限制模式
        self.crawled_count = 0  # 已爬取数量
        self._stop_flag = False  # 停止标志
        self.saved_count = 0  # 实际保存到数据库的数量（新增）
        self.duplicate_count = 0  # 去重数量
        self.max_crawl_limit = 1000  # 最大爬取限制（防止无限循环）
        self.proxy = proxy  # 代理地址
        self.skipped_count = 0  # 跳过的请求数量（用于统计）
    
    def start_requests(self):
        """
        生成初始请求 - 搜索页
        """
        # 构造搜索URL
        search_url = f"https://search.dangdang.com/?key={self.keyword}&act=input"
        
        # 设置请求头，模拟浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        # 构建请求参数
        request_kwargs = {
            "url": search_url,
            "headers": headers,
            "callback": self.parse_search_page
        }
        
        # 如果设置了代理，添加代理配置
        if self.proxy:
            request_kwargs["proxies"] = {
                "http": self.proxy,
                "https": self.proxy
            }
            print(f"🔒 使用代理: {self.proxy}")
        
        yield Request(**request_kwargs)
    
    def parse_search_page(self, request, response):
        """
        解析搜索结果页
        提取图书列表和详情页链接
        """
        print(f"📄 正在解析搜索页: {response.url}")
        
        # 提取图书列表
        # 方式1: 大图模式
        book_items = response.xpath('//ul[@class="bigimg"]/li')
        
        if not book_items:
            # 方式2: 列表模式
            book_items = response.xpath('//ul[@id="component_59"]/li')
        
        if not book_items:
            # 方式3: 其他可能的列表
            book_items = response.xpath('//div[@id="search_nature_rg"]//li[@class="line1"]')
        
        print(f"📚 找到 {len(book_items)} 个图书项")
        
        # 检查是否应该停止
        if self._stop_flag:
            # 已经停止，不再处理
            return
        
        if not self.is_unlimited and self.saved_count >= self.target_new_books:
            # 已达到目标，不再处理
            if self.skipped_count == 0:
                print(f"\n⏭️  已达到目标，跳过搜索页处理")
            return
        
        # 检查是否超过最大爬取限制
        if self.crawled_count >= self.max_crawl_limit:
            # 已达到限制
            if self.skipped_count == 0:
                print(f"\n⏭️  已达到最大爬取限制，跳过搜索页处理")
            return
        
        # 处理图书项
        count = 0
        for item in book_items:
            # 再次检查是否应该停止
            if self._stop_flag:
                # 已经停止，不再处理
                return
            
            if not self.is_unlimited and self.saved_count >= self.target_new_books:
                # 已达到目标，不再发起新请求
                return
            
            # 提取详情页链接
            detail_url = item.xpath('.//a[@class="pic"]/@href').extract_first() or \
                        item.xpath('.//p[@class="name"]/a/@href').extract_first() or \
                        item.xpath('.//a[@name="itemlist-title"]/@href').extract_first()
            
            # 提取基本信息（搜索页可见的信息）
            title = item.xpath('.//a[@class="pic"]/@title').extract_first() or \
                   item.xpath('.//p[@class="name"]/a/@title').extract_first() or \
                   item.xpath('.//a[@name="itemlist-title"]/@title').extract_first()
            
            price = item.xpath('.//p[@class="price"]/span[@class="search_now_price"]/text()').extract_first() or \
                   item.xpath('.//span[@class="search_now_price"]/text()').extract_first()
            
            if detail_url:
                count += 1
                
                # 再次检查（在发起请求前）
                if self._stop_flag or (not self.is_unlimited and self.saved_count >= self.target_new_books):
                    # 不再发起新请求
                    return
                # 构建请求参数
                request_kwargs = {
                    "url": detail_url,
                    "headers": request.headers,
                    "callback": self.parse_detail_page,
                    "meta": {"title": title, "price": price}
                }
                
                # 如果设置了代理，添加代理配置
                if self.proxy:
                    request_kwargs["proxies"] = {
                        "http": self.proxy,
                        "https": self.proxy
                    }
                
                # 发起详情页请求
                yield Request(**request_kwargs)
        
        # 判断是否需要翻页
        should_continue = False
        
        # 检查停止标志
        if self._stop_flag:
            # 已停止，不再翻页
            return
        
        if self.is_unlimited:
            # 无限制模式：继续翻页直到没有更多数据
            should_continue = True
        else:
            # 限制模式：如果新增数量未达到目标，继续翻页
            if self.saved_count < self.target_new_books and self.crawled_count < self.max_crawl_limit:
                should_continue = True
            else:
                if self.saved_count >= self.target_new_books:
                    # 已达到目标，不再翻页
                    return
        
        # 尝试翻页
        if should_continue:
            next_page = response.xpath('//li[@class="next"]/a/@href').extract_first()
            if next_page:
                if self.is_unlimited:
                    print(f"📄 无限制模式，继续翻页: {next_page}")
                else:
                    print(f"📄 新增数量 {self.saved_count}/{self.target_new_books}，继续翻页: {next_page}")
                
                # 构建请求参数
                request_kwargs = {
                    "url": response.urljoin(next_page),
                    "headers": request.headers,
                    "callback": self.parse_search_page
                }
                
                # 如果设置了代理，添加代理配置
                if self.proxy:
                    request_kwargs["proxies"] = {
                        "http": self.proxy,
                        "https": self.proxy
                    }
                
                yield Request(**request_kwargs)
            else:
                if self.is_unlimited:
                    print(f"📄 已到最后一页，无更多数据")
                else:
                    print(f"📄 已到最后一页，实际新增 {self.saved_count} 本（目标 {self.target_new_books} 本）")

    def parse_detail_page(self, request, response):
        """
        解析图书详情页
        提取完整的图书信息
        """
        try:
            # 检查是否应该停止（非无限制模式且已达到目标）
            if not self.is_unlimited and self.saved_count >= self.target_new_books:
                # 记录跳过数量
                self.skipped_count += 1
                # 只在第一次跳过时打印提示
                if self.skipped_count == 1:
                    print(f"\n⏭️  已达到目标新增数量 {self.target_new_books}，后续请求将被跳过...")
                return
            
            # 检查是否超过最大爬取限制
            if self.crawled_count >= self.max_crawl_limit:
                self.skipped_count += 1
                if self.skipped_count == 1:
                    print(f"\n⏭️  已达到最大爬取限制 {self.max_crawl_limit}，后续请求将被跳过...")
                return
            
            # 检查停止标志
            if self._stop_flag:
                self.skipped_count += 1
                return
            
            # 打印正在解析的URL
            print(f"🔍 正在解析详情页: {response.url}")
            
            # 从meta中获取搜索页的基本信息
            basic_title = request.meta.get("title", "")
            basic_price = request.meta.get("price", "")
            
            # 提取详情页信息
            # 图书标题 - 多种方式尝试
            title = response.xpath('//div[@class="name_info"]//h1/@title').extract_first() or \
                   response.xpath('//div[@class="name_info"]//h1/text()').extract_first() or \
                   response.xpath('//h1[@class="title"]/text()').extract_first() or \
                   basic_title
            
            # 作者 - 多种方式尝试
            author = response.xpath('//span[@id="author"]//a/text()').extract_first() or \
                    response.xpath('//div[@class="messbox_info"]//span[contains(text(),"作")]/following-sibling::a[1]/text()').extract_first() or \
                    response.xpath('//a[@name="itemlist-author"]/text()').extract_first() or \
                    response.xpath('//p[@class="author"]//a[1]/text()').extract_first()
            
            # 出版社 - 多种方式尝试
            publisher = response.xpath('//span[@id="publisher"]//a/text()').extract_first() or \
                       response.xpath('//div[@class="messbox_info"]//span[contains(text(),"出版社")]/following-sibling::a[1]/text()').extract_first() or \
                       response.xpath('//a[@name="P_cbs"]/text()').extract_first()
            
            # 出版时间 - 多种方式尝试
            publish_date = response.xpath('//span[@id="publish_time"]/text()').extract_first() or \
                          response.xpath('//div[@class="messbox_info"]//span[contains(text(),"出版时间")]/following-sibling::text()[1]').extract_first() or \
                          response.xpath('//span[@name="P_date"]/text()').extract_first()
            
            # 价格信息
            original_price = response.xpath('//span[@id="original-price"]/text()').extract_first() or \
                            response.xpath('//p[@class="price"]/span[@class="price_n"]/text()').extract_first()
            
            current_price = response.xpath('//span[@id="dd-price"]/text()').extract_first() or \
                           basic_price
            
            # 图书简介
            description = response.xpath('//div[@class="descrip"]//text()').extract_first() or \
                         response.xpath('//div[@id="content"]//div[@class="describe_detail"]//text()').extract_first() or \
                         response.xpath('//div[@class="book_intro"]//text()').extract_first()
            
            # ISBN - 多种方式尝试
            isbn = response.xpath('//li[contains(text(),"ISBN")]/text()').extract_first()
            if not isbn:
                isbn = response.xpath('//span[contains(text(),"ISBN")]/following-sibling::text()[1]').extract_first()
            if isbn:
                isbn = isbn.replace("ISBN：", "").replace("ISBN:", "").strip()
            
            # 评分 - 多种方式尝试
            rating = response.xpath('//span[@class="star_gray"]/text()').extract_first() or \
                    response.xpath('//div[@class="star"]//text()').extract_first() or \
                    response.xpath('//span[@class="score"]/text()').extract_first()
            
            # 评论数
            comment_count = response.xpath('//span[@id="comm_num_down"]/text()').extract_first() or \
                           response.xpath('//a[@id="comm_num"]/text()').extract_first()
            
            # 图书封面
            cover_image = response.xpath('//img[@id="largePic"]/@src').extract_first() or \
                         response.xpath('//div[@class="pic_box"]//img/@src').extract_first() or \
                         response.xpath('//img[@id="main-img"]/@src').extract_first()
            
            # 清理数据
            if title:
                title = title.strip()
            if author:
                author = author.strip()
            if publisher:
                publisher = publisher.strip()
            if publish_date:
                publish_date = publish_date.strip()
            if description:
                description = description.strip()
            
            # 构造图书数据
            book_data = {
                "标题": title if title else "",
                "作者": author if author else "",
                "出版社": publisher if publisher else "",
                "出版时间": publish_date if publish_date else "",
                "原价": original_price.strip() if original_price else "",
                "现价": current_price.strip() if current_price else "",
                "ISBN": isbn.strip() if isbn else "",
                "评分": rating.strip() if rating else "",
                "评论数": comment_count.strip() if comment_count else "",
                "简介": description if description else "",
                "封面图": cover_image.strip() if cover_image else "",
                "详情页URL": response.url,
                "搜索关键词": self.keyword  # 添加搜索关键词
            }
            
            # 打印提取的信息用于调试
            print(f"📖 提取信息: 标题={title}, 作者={author}, 出版社={publisher}, 出版时间={publish_date}, 评分={rating}")
            
            # 存储到内存
            self.results.append(book_data)
            self.crawled_count += 1
            
            # 存储到 MySQL（使用连接池）
            is_new = False
            if self.use_mysql:
                try:
                    result = MySQLPool.save_book(book_data)
                    if result['success']:
                        self.saved_count += 1
                        is_new = True
                        if self.is_unlimited:
                            print(f"💾 成功保存到数据库（已新增: {self.saved_count}，已爬取: {self.crawled_count}）")
                        else:
                            print(f"💾 成功保存到数据库（已新增: {self.saved_count}/{self.target_new_books}，已爬取: {self.crawled_count}）")
                    elif result['is_duplicate']:
                        self.duplicate_count += 1
                        print(f"⚠️ 图书重复，已跳过（去重: {self.duplicate_count}，已爬取: {self.crawled_count}）")
                    else:
                        print(f"⚠️ 保存到数据库失败: {result['message']}")
                except Exception as e:
                    print(f"⚠️ 保存到数据库失败: {e}")
            else:
                # 不使用数据库时，所有数据都算新增
                self.saved_count += 1
                is_new = True
            
            # 显示进度
            if self.is_unlimited:
                print(f"✅ 已爬取 {self.crawled_count} 本图书（新增: {self.saved_count}，重复: {self.duplicate_count}）")
            else:
                print(f"✅ 已爬取 {self.crawled_count} 本图书（新增: {self.saved_count}/{self.target_new_books}，重复: {self.duplicate_count}）")
            
            # 检查是否达到目标（非无限制模式）
            if not self.is_unlimited and self.saved_count >= self.target_new_books:
                # 只在刚达到目标时打印一次
                if not self._stop_flag:
                    print(f"\n{'='*60}")
                    print(f"🎉 已完成目标！成功新增 {self.saved_count} 本图书")
                    print(f"📊 总爬取: {self.crawled_count} 本，去重: {self.duplicate_count} 本")
                    print(f"🛑 正在停止爬虫...")
                    print(f"{'='*60}\n")
                    # 主动停止爬虫
                    self._stop_crawling()
                return
        
        except Exception as e:
            print(f"❌ 解析详情页失败: {e}")
            import traceback
            traceback.print_exc()
            # 继续处理其他页面，不中断爬虫
    
    def _stop_crawling(self):
        """停止爬虫的内部方法"""
        if self._stop_flag:
            # 已经停止过了，不重复打印
            return
        
        try:
            self._stop_flag = True
            print("🛑 爬虫已停止")
            
            # 打印跳过统计
            if self.skipped_count > 0:
                print(f"📊 跳过了 {self.skipped_count} 个已在队列中的请求")
            
            # 调用父类的停止方法
            if hasattr(self, '_spider') and self._spider:
                self._spider.stop()
        except Exception as e:
            print(f"⚠️ 停止爬虫时出错: {e}")
    
    def stop(self):
        """停止爬虫（公共方法）"""
        self._stop_crawling()


def run_spider(keyword: str, thread_count: int = 3, use_mysql: bool = True, mysql_config: Optional[Dict] = None, max_books: int = 20, proxy: Optional[str] = None) -> Dict:
    """
    运行爬虫并返回结果
    :param keyword: 搜索关键词
    :param thread_count: 线程数
    :param use_mysql: 是否使用 MySQL 存储（默认 True）
    :param mysql_config: MySQL 配置字典（用于初始化连接池）
    :param max_books: 最大爬取图书数量（默认 20）
    :return: 图书数据列表
    """
    import time
    import threading
    
    print("\n" + "="*60)
    print(f"🚀 开始爬取关键词: {keyword}")
    print(f"📊 线程数: {thread_count}")
    if max_books == 0:
        print(f"📚 爬取模式: 无限制（爬取所有数据）")
    else:
        print(f"📚 目标新增数量: {max_books} 本")
        print(f"📌 说明: 会持续爬取直到新增 {max_books} 本到数据库（自动去重）")
    print(f"💾 数据库存储: {'启用' if use_mysql else '禁用'}")
    if proxy:
        print(f"🔒 代理设置: {proxy}")
    else:
        print(f"🔒 代理设置: 未使用")
    print("="*60 + "\n")
    
    # 如果使用 MySQL，先初始化连接池
    if use_mysql:
        if mysql_config is None:
            # 如果没有提供配置，使用默认配置
            from db_config import MYSQL_CONFIG
            mysql_config = MYSQL_CONFIG
        
        try:
            MySQLPool.initialize(
                host=mysql_config.get('host', 'localhost'),
                port=mysql_config.get('port', 3306),
                user=mysql_config.get('user', 'root'),
                password=mysql_config.get('password', ''),
                database=mysql_config.get('database', 'dangdang_books'),
                mincached=2,
                maxcached=10,
                maxconnections=20
            )
        except Exception as e:
            print(f"⚠️ 连接池初始化失败: {e}")
            use_mysql = False
    
    spider = None
    spider_thread = None
    
    try:
        spider = DangDangSpider(
            keyword=keyword, 
            thread_count=thread_count,
            use_mysql=use_mysql,
            max_books=max_books,
            proxy=proxy
        )
        
        print(f"🕷️ 爬虫开始运行...")
        
        # 在单独的线程中运行爬虫（非 daemon，确保正常完成）
        def run_spider_thread():
            try:
                spider.start()
            except Exception as e:
                print(f"⚠️ 爬虫线程异常: {e}")
        
        spider_thread = threading.Thread(target=run_spider_thread, daemon=False)
        spider_thread.start()
        
        # 等待爬虫完成或达到目标
        max_wait_time = 180  # 最多等待180秒
        wait_interval = 0.5  # 每0.5秒检查一次
        elapsed = 0
        
        print(f"⏳ 等待爬虫完成...")
        
        while elapsed < max_wait_time:
            # 检查是否达到目标数量（非无限制模式）
            if not spider.is_unlimited and spider.saved_count >= max_books:
                print(f"\n{'='*60}")
                print(f"✅ 已达到目标新增数量 {max_books}，准备停止爬虫")
                print(f"📊 当前状态: 爬取 {spider.crawled_count} 本，新增 {spider.saved_count} 本，去重 {spider.duplicate_count} 本")
                print(f"{'='*60}\n")
                
                # 设置停止标志
                spider._stop_flag = True
                
                # 主动停止爬虫
                try:
                    spider._stop_crawling()
                except Exception as e:
                    print(f"⚠️ 停止爬虫时出错: {e}")
                
                # 等待线程结束（最多5秒）
                print(f"⏳ 等待爬虫线程结束...")
                spider_thread.join(timeout=5)
                
                if spider_thread.is_alive():
                    print(f"⚠️ 爬虫线程未能及时结束，强制返回结果")
                else:
                    print(f"✅ 爬虫线程已正常结束")
                
                break
            
            # 检查线程是否还活着
            if not spider_thread.is_alive():
                print(f"✅ 爬虫线程已自然结束")
                break
            
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        if elapsed >= max_wait_time:
            print(f"⚠️ 等待超时（{max_wait_time}秒），强制返回结果")
            spider._stop_flag = True
            try:
                spider._stop_crawling()
            except:
                pass
        
        print(f"🕷️ 爬虫运行结束")
        
        result_count = len(spider.results) if spider and spider.results else 0
        saved_count = spider.saved_count if spider else 0
        duplicate_count = spider.duplicate_count if spider else 0
        
        print("\n" + "="*60)
        print(f"✅ 爬取完成！")
        print(f"📊 爬取数量: {result_count} 本")
        print(f"💾 保存数量: {saved_count} 本")
        print(f"🔄 去重数量: {duplicate_count} 本")
        print(f"📌 去重关键词: 标题 + 作者")
        if use_mysql:
            print(f"💾 数据已保存到 MySQL 数据库")
        print("="*60 + "\n")
        
        # 确保返回结果（包含统计信息）
        results = spider.results if spider and spider.results else []
        print(f"🔚 准备返回 {len(results)} 条结果")
        
        # 返回结果和统计信息
        return {
            'books': results,
            'total_crawled': result_count,
            'total_saved': saved_count,
            'total_duplicates': duplicate_count,
            'dedup_key': '标题 + 作者'
        }
    
    except Exception as e:
        print(f"\n❌ 爬虫运行出错: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        # 即使出错也返回已爬取的结果
        if spider and spider.results:
            print(f"⚠️ 返回已爬取的 {len(spider.results)} 本图书")
            return {
                'books': spider.results,
                'total_crawled': len(spider.results),
                'total_saved': spider.saved_count if spider else 0,
                'total_duplicates': spider.duplicate_count if spider else 0,
                'dedup_key': '标题 + 作者'
            }
        return {
            'books': [],
            'total_crawled': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'dedup_key': '标题 + 作者'
        }
    
    finally:
        print("🔚 run_spider 函数执行完毕，即将返回")


if __name__ == "__main__":
    # 命令行模式
    keyword = input("请输入搜索关键词: ").strip()
    if not keyword:
        keyword = "Python"  # 默认关键词
    
    # 询问是否使用 MySQL（默认使用）
    use_mysql_input = input("是否使用 MySQL 存储? (y/n, 默认y): ").strip().lower()
    use_mysql = use_mysql_input != 'n'  # 只有输入 n 才不使用
    
    # 运行爬虫（使用默认配置）
    results = run_spider(keyword, use_mysql=use_mysql)
    
    # 打印结果
    print(f"\n总共爬取到 {len(results)} 本图书")
    if use_mysql:
        print("✅ 数据已保存到 MySQL 数据库")
    
    for idx, book in enumerate(results, 1):
        print(f"\n{idx}. {book.get('标题', '未知')}")
        print(f"   作者: {book.get('作者', '未知')}")
        print(f"   价格: {book.get('现价', '未知')}")
