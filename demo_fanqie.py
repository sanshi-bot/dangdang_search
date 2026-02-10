"""
番茄小说爬虫功能演示
"""

from fanqie import run_recommend_spider, run_detail_spider, run_author_spider
import time


def demo_recommend():
    """演示：爬取推荐列表"""
    print("\n" + "=" * 60)
    print("演示 1：爬取推荐列表")
    print("=" * 60)
    print("功能：爬取番茄小说推荐页面，获取书名和书籍ID")
    print()
    
    print("开始爬取推荐列表...")
    results = run_recommend_spider(use_mysql=False, max_books=5)
    
    if results['books']:
        print(f"\n✅ 成功爬取 {len(results['books'])} 本推荐书籍")
        print("\n推荐书籍列表:")
        print("-" * 60)
        for i, book in enumerate(results['books'], 1):
            print(f"{i}. {book['书名']}")
            print(f"   书籍ID: {book['书籍ID']}")
            print(f"   详情页: {book['详情页URL']}")
            print()
    else:
        print("❌ 未获取到推荐书籍")
    
    return results


def demo_detail():
    """演示：爬取书籍详情"""
    print("\n" + "=" * 60)
    print("演示 2：爬取书籍详情")
    print("=" * 60)
    print("功能：根据书名或ID爬取完整的书籍详情信息")
    print()
    
    # 使用测试书籍ID
    test_book_id = "7276384138653862966"
    
    print(f"开始爬取书籍详情 (ID: {test_book_id})...")
    result = run_detail_spider(book_id=test_book_id, use_mysql=False)
    
    if result['success'] and result['book']:
        book = result['book']
        print(f"\n✅ 成功获取书籍详情")
        print("\n书籍信息:")
        print("-" * 60)
        print(f"书名: {book['标题']}")
        print(f"作者: {book['作者']}")
        print(f"分类: {book['分类']}")
        print(f"状态: {book['状态']}")
        print(f"字数: {book['字数']}")
        print(f"章节数: {book['章节数']}")
        print(f"最新章节: {book['最新章节']}")
        print(f"更新时间: {book['更新时间']}")
        print(f"\n简介: {book['简介'][:100]}...")
        print("-" * 60)
    else:
        print("❌ 未获取到书籍详情")
    
    return result


def demo_author():
    """演示：搜索作者书籍"""
    print("\n" + "=" * 60)
    print("演示 3：搜索作者书籍")
    print("=" * 60)
    print("功能：搜索指定作者的所有作品")
    print()
    
    # 使用测试作者名
    test_author = "三九音域"
    
    print(f"开始搜索作者: {test_author}...")
    results = run_author_spider(author_name=test_author, use_mysql=False, max_books=5)
    
    if results['books']:
        print(f"\n✅ 找到 {len(results['books'])} 本 {test_author} 的作品")
        print(f"\n{test_author} 的作品列表:")
        print("-" * 60)
        for i, book in enumerate(results['books'], 1):
            print(f"{i}. {book['书名']}")
            print(f"   书籍ID: {book['书籍ID']}")
            print(f"   作者: {book['作者']}")
            print()
    else:
        print(f"❌ 未找到 {test_author} 的作品")
    
    return results


def main():
    """主演示函数"""
    print("\n" + "=" * 60)
    print("番茄小说爬虫功能演示")
    print("=" * 60)
    print("本演示将展示三大核心功能：")
    print("1. 推荐列表爬取")
    print("2. 书籍详情爬取")
    print("3. 作者搜索")
    print("=" * 60)
    
    try:
        # 演示1：推荐列表
        demo_recommend()
        time.sleep(2)
        
        # 演示2：书籍详情
        demo_detail()
        time.sleep(2)
        
        # 演示3：作者搜索
        demo_author()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n说明：")
        print("- 以上演示未连接数据库（use_mysql=False）")
        print("- 实际使用时可以启用数据库存储")
        print("- 推荐列表只包含书名和ID，详情需要单独爬取")
        print("- 作者搜索会建立作者与书籍的关联关系")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
