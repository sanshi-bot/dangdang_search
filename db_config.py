"""
数据库配置文件
用于配置 MySQL 连接参数
"""

# MySQL 数据库配置
MYSQL_CONFIG = {
    'host': 'localhost',      # MySQL 服务器地址
    'port': 3306,             # MySQL 端口
    'user': 'root',           # 用户名
    'password': '123456',           # 密码（请修改为实际密码）
    'database': 'dangdang_books'  # 数据库名
}

# 是否启用数据库存储
USE_MYSQL = True  # 设置为 True 启用 MySQL 存储，False 则只使用内存存储
