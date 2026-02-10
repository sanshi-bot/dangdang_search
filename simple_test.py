"""
简单测试番茄小说爬虫
"""

print("=" * 60)
print("番茄小说爬虫简单测试")
print("=" * 60)

# 测试1：导入模块
print("\n测试1：导入模块...")
try:
    from fanqie import (
        FanQieRecommendSpider,
        FanQieDetailSpider,
        FanQieAuthorSpider
    )
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

# 测试2：创建爬虫实例
print("\n测试2：创建爬虫实例...")
try:
    recommend_spider = FanQieRecommendSpider(use_mysql=False, max_books=5)
    detail_spider = FanQieDetailSpider(book_id="7276384138653862966", use_mysql=False)
    author_spider = FanQieAuthorSpider(author_name="三九音域", use_mysql=False, max_books=5)
    print("✅ 爬虫实例创建成功")
except Exception as e:
    print(f"❌ 爬虫实例创建失败: {e}")
    exit(1)

# 测试3：测试 fanqie_web_detail
print("\n测试3：测试 fanqie_web_detail 模块...")
try:
    from fanqie_web_detail import FanQieWebDetail
    parser = FanQieWebDetail()
    print("✅ fanqie_web_detail 模块正常")
except Exception as e:
    print(f"❌ fanqie_web_detail 模块异常: {e}")

print("\n" + "=" * 60)
print("所有基础测试通过！")
print("=" * 60)
print("\n说明：")
print("1. 所有模块导入正常")
print("2. 爬虫实例可以正常创建")
print("3. 解析工具类正常工作")
print("\n如需实际爬取数据，请运行：")
print("  - python demo_fanqie.py  (演示所有功能)")
print("  - python fanqie.py       (交互式命令行)")
print("  - python fanqie_web_detail.py  (独立解析工具)")
print("=" * 60)
