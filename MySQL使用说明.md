# MySQL 数据库使用说明

## 1. 安装 MySQL

### Windows 系统
1. 下载 MySQL 安装包：https://dev.mysql.com/downloads/mysql/
2. 运行安装程序，按照向导完成安装
3. 记住设置的 root 密码

### 或使用 XAMPP/WAMP
- XAMPP: https://www.apachefriends.org/
- WAMP: https://www.wampserver.com/

## 2. 安装 Python MySQL 依赖

运行安装脚本：
```bash
install_mysql.bat
```

或手动安装：
```bash
pip install pymysql
```

## 3. 配置数据库连接

编辑 `db_config.py` 文件，修改数据库连接信息：

```python
MYSQL_CONFIG = {
    'host': 'localhost',      # MySQL 服务器地址
    'port': 3306,             # MySQL 端口
    'user': 'root',           # 用户名
    'password': '你的密码',    # 密码
    'database': 'dangdang_books'  # 数据库名
}

USE_MYSQL = True  # 启用 MySQL 存储
```

## 4. 数据库表结构

程序会自动创建以下表结构：

```sql
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,           -- 标题
    author VARCHAR(200),                   -- 作者
    publisher VARCHAR(200),                -- 出版社
    publish_date VARCHAR(50),              -- 出版时间
    original_price VARCHAR(50),            -- 原价
    current_price VARCHAR(50),             -- 现价
    isbn VARCHAR(50),                      -- ISBN（唯一）
    rating VARCHAR(20),                    -- 评分
    comment_count VARCHAR(50),             -- 评论数
    description TEXT,                      -- 简介
    cover_image VARCHAR(500),              -- 封面图
    detail_url VARCHAR(500),               -- 详情页URL
    search_keyword VARCHAR(100),           -- 搜索关键词
    created_at TIMESTAMP,                  -- 创建时间
    updated_at TIMESTAMP                   -- 更新时间
)
```

## 5. 使用方式

### 方式1：命令行模式

```bash
python dangdang.py
```

程序会询问是否使用 MySQL 存储，输入 `y` 启用。

### 方式2：Web API 模式

```bash
python backend/api.py
```

API 会自动使用 `db_config.py` 中的配置。

### 方式3：一键启动

```bash
start_all.bat
```

## 6. 数据库操作

### 测试数据库连接

```bash
python mysql_db.py
```

### 查看数据库中的图书

使用 MySQL 客户端或工具（如 Navicat、phpMyAdmin）：

```sql
-- 查看所有图书
SELECT * FROM books;

-- 按关键词查询
SELECT * FROM books WHERE search_keyword = 'Python';

-- 统计图书数量
SELECT COUNT(*) FROM books;

-- 按关键词统计
SELECT search_keyword, COUNT(*) as count 
FROM books 
GROUP BY search_keyword;
```

## 7. 数据库管理

### 清空所有数据

```python
from mysql_db import MySQLDB

db = MySQLDB(
    host='localhost',
    user='root',
    password='你的密码',
    database='dangdang_books'
)

db.clear_all_books()
db.close()
```

### 删除指定图书

```python
db.delete_book(book_id=1)
```

### 获取统计信息

```python
stats = db.get_statistics()
print(f"总图书数: {stats['total_books']}")
print("关键词统计:", stats['keywords'])
```

## 8. 常见问题

### Q: 连接失败怎么办？
A: 检查以下几点：
1. MySQL 服务是否启动
2. 用户名和密码是否正确
3. 端口是否正确（默认 3306）
4. 防火墙是否允许连接

### Q: 如何修改数据库名？
A: 修改 `db_config.py` 中的 `database` 参数

### Q: 数据会重复吗？
A: 不会，程序使用 ISBN 作为唯一标识，相同 ISBN 的图书会更新而不是重复插入

### Q: 如何禁用数据库存储？
A: 在 `db_config.py` 中设置 `USE_MYSQL = False`

## 9. 性能优化

- 数据库已创建索引：ISBN（唯一）、搜索关键词、标题
- 使用批量插入可提高性能
- 定期清理旧数据

## 10. 备份与恢复

### 备份数据库

```bash
mysqldump -u root -p dangdang_books > backup.sql
```

### 恢复数据库

```bash
mysql -u root -p dangdang_books < backup.sql
```
