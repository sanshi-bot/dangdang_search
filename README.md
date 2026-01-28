# 当当网图书爬虫项目

## 项目简介

这是一个基于 Python 的当当网图书爬虫项目，使用 feapder 框架爬取图书数据，并通过 FastAPI 提供 Web API 接口。**默认使用 MySQL 数据库存储数据**，支持多线程安全访问。

## 主要功能

- 🕷️ 爬取当当网图书信息（标题、作者、价格、ISBN、评分等）
- 💾 **自动保存到 MySQL 数据库**（使用连接池技术）
- 🌐 提供 Web API 接口
- 🎨 美观的前端界面
- 🔍 支持关键词搜索和数据展示

## 技术栈

- **爬虫框架**: feapder
- **后端框架**: FastAPI
- **前端框架**: Vue.js 3
- **数据库**: MySQL（使用 DBUtils 连接池）
- **HTTP 客户端**: Axios

## 快速开始

### 1. 安装依赖

```bash
# 安装所有依赖
install_dependencies.bat

# 或单独安装 MySQL 依赖
install_mysql.bat
```

### 2. 配置数据库

编辑 `db_config.py` 文件，设置 MySQL 密码：

```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '你的MySQL密码',  # 修改这里
    'database': 'dangdang_books'
}

USE_MYSQL = True  # 默认启用 MySQL 存储
```

### 3. 启动应用

```bash
# 一键启动（后端 + 前端）
start_all.bat
```

或分别启动：

```bash
# 启动后端
start_backend.bat

# 启动前端
start_frontend.bat
```

## 使用说明

### 前端界面

1. **开始爬取**：输入关键词，点击"开始爬取"按钮，从当当网爬取数据并保存到数据库
2. **展示数据库数据**：点击"展示数据库数据"按钮，从数据库读取已保存的图书数据

### API 接口

- `POST /api/crawl` - 爬取图书并保存到数据库
- `GET /api/books` - 从数据库获取图书列表
- `GET /api/stats` - 获取统计信息
- `GET /health` - 健康检查

### 命令行模式

```bash
python dangdang.py
```

输入关键词后，默认会保存到 MySQL 数据库。

## 数据库连接池

项目使用 DBUtils 实现 MySQL 连接池，具有以下特性：

- ✅ 线程安全，支持多线程并发访问
- ✅ 连接复用，提高性能
- ✅ 自动管理连接生命周期
- ✅ 配置灵活（最小连接数、最大连接数等）

连接池配置：
- 最小空闲连接：2
- 最大空闲连接：10
- 最大连接数：20

## 项目结构

```
├── dangdang.py              # 爬虫核心代码
├── mysql_pool.py            # MySQL 连接池
├── mysql_db.py              # MySQL 数据库操作（旧版，已被连接池替代）
├── db_config.py             # 数据库配置
├── backend/
│   └── api.py               # FastAPI 后端服务
├── frontend/
│   ├── index.html           # 前端页面
│   ├── app.js               # Vue.js 应用
│   └── style.css            # 样式文件
└── requirements.txt         # Python 依赖
```

## 注意事项

1. **MySQL 服务必须启动**
2. **配置正确的数据库密码**（在 `db_config.py` 中）
3. 数据库和表会在首次运行时自动创建
4. 使用 ISBN 作为唯一标识，避免重复数据

## 常见问题

### Q: 如何禁用 MySQL 存储？
A: 在 `db_config.py` 中设置 `USE_MYSQL = False`

### Q: 连接池初始化失败？
A: 检查 MySQL 服务是否启动，密码是否正确

### Q: 如何修改连接池配置？
A: 在 `mysql_pool.py` 的 `initialize` 方法中修改参数

## 文档

- [MySQL使用说明.md](MySQL使用说明.md) - MySQL 数据库详细说明
- [前端使用说明.md](前端使用说明.md) - 前端功能使用指南
- [项目结构.md](项目结构.md) - 项目文件结构说明

## 许可证

MIT License
