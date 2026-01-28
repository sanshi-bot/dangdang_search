-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS dangdang_books 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE dangdang_books;

-- 删除旧表（如果需要重建）
-- DROP TABLE IF EXISTS books;

-- 创建图书信息表
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
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
    
    -- 唯一索引：标题+作者组合唯一（实现去重）
    UNIQUE KEY unique_title_author (title(255), author(100)) COMMENT '标题+作者唯一索引',
    
    -- 普通索引
    INDEX idx_keyword (search_keyword) COMMENT '搜索关键词索引',
    INDEX idx_title (title(100)) COMMENT '标题索引',
    INDEX idx_created_at (created_at) COMMENT '创建时间索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书信息表';

-- 显示表结构
DESCRIBE books;

-- 显示索引
SHOW INDEX FROM books;

-- 查看数据统计
SELECT COUNT(*) as total FROM books;
