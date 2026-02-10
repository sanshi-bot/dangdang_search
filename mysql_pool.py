"""
MySQL 连接池模块
使用 DBUtils 实现线程安全的数据库连接池
"""

from dbutils.pooled_db import PooledDB
import pymysql
from typing import Dict, List, Optional


class MySQLPool:
    """MySQL 连接池类"""
    
    _pool = None  # 连接池单例
    
    @classmethod
    def close_pool(cls):
        """关闭连接池"""
        if cls._pool:
            try:
                cls._pool.close()
                cls._pool = None
                # print("✅ MySQL 连接池已关闭")
            except Exception as e:
                # print(f"⚠️ 关闭 MySQL 连接池失败: {e}")
                pass
    
    @classmethod
    def initialize(cls, host='localhost', port=3306, user='root', password='123456', database='dangdang_books', 
                   mincached=2, maxcached=10, maxconnections=20):
        """
        初始化连接池（只需调用一次）
        :param host: MySQL 服务器地址
        :param port: MySQL 端口
        :param user: 用户名
        :param password: 密码
        :param database: 数据库名
        :param mincached: 连接池中空闲连接的最小数量
        :param maxcached: 连接池中空闲连接的最大数量
        :param maxconnections: 连接池允许的最大连接数
        """
        if cls._pool is None:
            try:
                # print(f"🔄 正在连接 MySQL 服务器: {host}:{port}")
                
                # 先连接到 MySQL 服务器（不指定数据库）
                temp_conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    charset='utf8mb4'
                )
                
                # print(f"✅ 成功连接到 MySQL 服务器")
                
                # 检查数据库是否存在
                with temp_conn.cursor() as cursor:
                    cursor.execute("SHOW DATABASES LIKE %s", (database,))
                    db_exists = cursor.fetchone()
                    
                    if not db_exists:
                        # print(f"⚠️ 数据库 '{database}' 不存在，正在创建...")
                        pass
                        cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        temp_conn.commit()
                        # print(f"✅ 数据库 '{database}' 创建成功")
                    else:
                        # print(f"✅ 数据库 '{database}' 已存在")
                        pass
                
                temp_conn.close()
                
                # 创建连接池
                # print(f"🔄 正在创建连接池...")
                cls._pool = PooledDB(
                    creator=pymysql,
                    maxconnections=maxconnections,
                    mincached=mincached,
                    maxcached=maxcached,
                    blocking=True,
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=False  # 显式设置为手动提交，确保事务控制
                )
                
                # print(f"✅ 连接池创建成功")
                
                # 创建表
                # print(f"🔄 正在检查/创建数据表...")
                cls._create_table()
                
                # print(f"✅ MySQL 连接池初始化完成: {host}:{port}/{database}")
                # print(f"   连接池配置: 最小空闲={mincached}, 最大空闲={maxcached}, 最大连接={maxconnections}")
                
            except pymysql.err.OperationalError as e:
                error_code = e.args[0]
                if error_code == 1045:
                    # print(f"❌ MySQL 连接失败: 用户名或密码错误")
                    pass
                    # print(f"   请检查 db_config.py 中的用户名和密码配置")
                elif error_code == 2003:
                    # print(f"❌ MySQL 连接失败: 无法连接到服务器 {host}:{port}")
                    pass
                    # print(f"   请确保 MySQL 服务已启动")
                else:
                    # print(f"❌ MySQL 连接失败: {e}")
                    pass
                raise
            except Exception as e:
                # print(f"❌ MySQL 连接池初始化失败: {e}")
                pass
                import traceback
                traceback.print_exc()
                raise
    
    @classmethod
    def _create_table(cls):
        """创建图书数据表（带唯一索引）"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(500) NOT NULL COMMENT '标题',
            author VARCHAR(200) DEFAULT '' COMMENT '作者',
            publisher VARCHAR(200) DEFAULT '' COMMENT '出版社',
            publish_date VARCHAR(50) DEFAULT '' COMMENT '出版时间',
            original_price VARCHAR(50) DEFAULT '' COMMENT '原价',
            current_price VARCHAR(50) DEFAULT '' COMMENT '现价',
            isbn VARCHAR(50) DEFAULT '' COMMENT 'ISBN',
            rating VARCHAR(20) DEFAULT '' COMMENT '评分',
            comment_count VARCHAR(50) DEFAULT '' COMMENT '评论数',
            description TEXT COMMENT '简介',
            cover_image VARCHAR(500) DEFAULT '' COMMENT '封面图',
            detail_url VARCHAR(500) DEFAULT '' COMMENT '详情页URL',
            search_keyword VARCHAR(100) DEFAULT '' COMMENT '搜索关键词',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            UNIQUE KEY unique_title_author (title(255), author(100)) COMMENT '标题+作者唯一索引',
            INDEX idx_keyword (search_keyword),
            INDEX idx_title (title(100))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书信息表'
        """
        
        try:
            conn = cls.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                conn.commit()
                # print("✅ 数据表创建/检查完成")
                
                # 检查并添加唯一索引（如果表已存在但没有索引）
                check_index_sql = """
                SELECT COUNT(*) as count 
                FROM information_schema.statistics 
                WHERE table_schema = DATABASE() 
                AND table_name = 'books' 
                AND index_name = 'unique_title_author'
                """
                cursor.execute(check_index_sql)
                result = cursor.fetchone()
                
                if result and result['count'] == 0:
                    # print("⚠️ 检测到表中缺少唯一索引，正在添加...")
                    pass
                    add_index_sql = """
                    ALTER TABLE books 
                    ADD UNIQUE KEY unique_title_author (title(255), author(100))
                    """
                    try:
                        cursor.execute(add_index_sql)
                        conn.commit()
                        # print("✅ 唯一索引添加成功")
                    except Exception as e:
                        if "Duplicate key name" in str(e):
                            # print("✅ 唯一索引已存在")
                            pass
                        else:
                            # print(f"⚠️ 添加唯一索引失败: {e}")
                            pass
                else:
                    # print("✅ 唯一索引已存在")
                    pass
                    
            conn.close()
        except Exception as e:
            # print(f"❌ 创建表失败: {e}")
            pass
            raise
    
    @classmethod
    def get_connection(cls):
        """
        从连接池获取一个连接
        :return: 数据库连接对象
        """
        if cls._pool is None:
            raise Exception("连接池未初始化，请先调用 MySQLPool.initialize()")
        return cls._pool.connection()
    
    @classmethod
    def save_book(cls, book_data: Dict) -> Dict:
        """
        保存单本图书数据（带去重检查）
        使用唯一索引实现数据库层面的去重
        :param book_data: 图书数据字典
        :return: 保存结果字典 {'success': bool, 'is_duplicate': bool, 'message': str}
        """
        # 使用 INSERT IGNORE 来忽略重复数据
        sql = """
        INSERT IGNORE INTO books (
            title, author, publisher, publish_date, 
            original_price, current_price, isbn, rating, 
            comment_count, description, cover_image, 
            detail_url, search_keyword
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        conn = None
        cursor = None
        try:
            title = book_data.get('标题', '未知')
            author = book_data.get('作者', '').strip()
            isbn = book_data.get('ISBN', '').strip()
            
            # 如果 ISBN 为空，设置为 None
            if not isbn:
                isbn = None
            
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            # 执行插入
            cursor.execute(sql, (
                book_data.get('标题', ''),
                author,
                book_data.get('出版社', ''),
                book_data.get('出版时间', ''),
                book_data.get('原价', ''),
                book_data.get('现价', ''),
                isbn,
                book_data.get('评分', ''),
                book_data.get('评论数', ''),
                book_data.get('简介', ''),
                book_data.get('封面图', ''),
                book_data.get('详情页URL', ''),
                book_data.get('搜索关键词', '')
            ))
            
            conn.commit()
            
            # 检查是否插入成功（affected_rows = 0 表示重复）
            affected_rows = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                # 插入成功
                # print(f"✅ 成功保存图书: {title}")
                return {
                    'success': True,
                    'is_duplicate': False,
                    'message': f'成功保存: {title}'
                }
            else:
                # 重复数据，被忽略
                # print(f"⚠️ 图书已存在（去重）: {title} - {author}")
                return {
                    'success': False,
                    'is_duplicate': True,
                    'message': f'图书已存在: {title}'
                }
            
        except pymysql.err.IntegrityError as e:
            # 唯一索引冲突（虽然用了 INSERT IGNORE，但还是捕获一下）
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            
            title = book_data.get('标题', '未知')
            # print(f"⚠️ 图书已存在（唯一索引冲突）: {title}")
            
            return {
                'success': False,
                'is_duplicate': True,
                'message': f'图书已存在: {title}'
            }
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            
            title = book_data.get('标题', '未知')
            # print(f"❌ 保存图书失败 [{title}]: {e}")
            
            return {
                'success': False,
                'is_duplicate': False,
                'message': f'保存失败: {str(e)}'
            }
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    @classmethod
    def get_all_books(cls, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        获取所有图书（分页，按价格排序）
        :param limit: 每页数量
        :param offset: 偏移量
        :return: 图书数据列表
        """
        sql = """
        SELECT * FROM books 
        ORDER BY 
            CAST(REPLACE(REPLACE(current_price, '¥', ''), ',', '') AS DECIMAL(10,2)) ASC,
            created_at DESC 
        LIMIT %s OFFSET %s
        """
        
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (limit, offset))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return [cls._format_book(row) for row in results]
        except Exception as e:
            # print(f"❌ 获取所有图书失败: {e}")
            pass
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    @classmethod
    def get_books_by_keyword(cls, keyword: str) -> List[Dict]:
        """
        根据搜索关键词获取图书（按价格排序）
        :param keyword: 搜索关键词
        :return: 图书数据列表
        """
        sql = """
        SELECT * FROM books 
        WHERE search_keyword = %s 
        ORDER BY 
            CAST(REPLACE(REPLACE(current_price, '¥', ''), ',', '') AS DECIMAL(10,2)) ASC,
            created_at DESC
        """
        
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (keyword,))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return [cls._format_book(row) for row in results]
        except Exception as e:
            # print(f"❌ 获取图书失败: {e}")
            pass
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    @classmethod
    def get_book_count(cls) -> int:
        """
        获取图书总数
        :return: 图书数量
        """
        sql = "SELECT COUNT(*) as count FROM books"
        
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['count'] if result else 0
        except Exception as e:
            # print(f"❌ 获取图书数量失败: {e}")
            pass
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    @classmethod
    def get_statistics(cls) -> Dict:
        """
        获取统计信息
        :return: 统计数据字典
        """
        try:
            stats = {
                'total_books': cls.get_book_count(),
                'keywords': []
            }
            
            sql = """
            SELECT search_keyword, COUNT(*) as count 
            FROM books 
            WHERE search_keyword != ''
            GROUP BY search_keyword 
            ORDER BY count DESC
            """
            
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            stats['keywords'] = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return stats
        except Exception as e:
            # print(f"❌ 获取统计信息失败: {e}")
            pass
            return {'total_books': 0, 'keywords': []}
    
    @classmethod
    def _format_book(cls, row: Dict) -> Dict:
        """
        格式化数据库行为图书数据字典
        :param row: 数据库行
        :return: 格式化后的图书数据
        """
        if not row:
            return {}
        
        return {
            'id': row.get('id'),
            '标题': row.get('title', ''),
            '作者': row.get('author', ''),
            '出版社': row.get('publisher', ''),
            '出版时间': row.get('publish_date', ''),
            '原价': row.get('original_price', ''),
            '现价': row.get('current_price', ''),
            'ISBN': row.get('isbn', ''),
            '评分': row.get('rating', ''),
            '评论数': row.get('comment_count', ''),
            '简介': row.get('description', ''),
            '封面图': row.get('cover_image', ''),
            '详情页URL': row.get('detail_url', ''),
            '搜索关键词': row.get('search_keyword', ''),
            '创建时间': row.get('created_at'),
            '更新时间': row.get('updated_at')
        }
