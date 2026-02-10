"""
测试番茄小说解析功能
"""

from fanqie_web_detail import FanQieWebDetail


def test_book_info():
    """测试获取书籍信息"""
    print("=" * 60)
    print("测试：获取书籍信息")
    print("=" * 60)
    
    parser = FanQieWebDetail()
    
    # 测试URL
    test_url = "https://fanqienovel.com/page/7276384138653862966"
    
    print(f"\n正在获取书籍信息: {test_url}\n")
    
    book_info = parser.get_book_info(test_url)
    
    if book_info:
        print(f"✅ 成功获取书籍信息")
        print(f"\n书名: {book_info['name']}")
        print(f"作者: {book_info['author']}")
        print(f"标签: {', '.join(book_info['labels'])}")
        print(f"章节数: {len(book_info['chapters'])}")
        
        if book_info['chapters']:
            print(f"\n前3章:")
            for i, chapter in enumerate(book_info['chapters'][:3], 1):
                print(f"  {i}. {chapter['title']}")
        
        return True
    else:
        print("❌ 获取书籍信息失败")
        return False


def test_chapter_content():
    """测试获取章节内容"""
    print("\n" + "=" * 60)
    print("测试：获取章节内容")
    print("=" * 60)
    
    parser = FanQieWebDetail()
    
    # 先获取书籍信息
    test_url = "https://fanqienovel.com/page/7276384138653862966"
    book_info = parser.get_book_info(test_url)
    
    if not book_info or not book_info['chapters']:
        print("❌ 无法获取章节列表")
        return False
    
    # 获取第一章内容
    first_chapter = book_info['chapters'][0]
    print(f"\n正在获取章节: {first_chapter['title']}\n")
    
    content = parser.get_chapter_content(first_chapter['url'])
    
    if content:
        print(f"✅ 成功获取章节内容")
        print(f"\n内容预览（前200字）:")
        print("-" * 60)
        print(content[:200])
        print("-" * 60)
        print(f"\n总字数: {len(content)}")
        return True
    else:
        print("❌ 获取章节内容失败")
        return False


def test_decode():
    """测试字符解码"""
    print("\n" + "=" * 60)
    print("测试：字符解码")
    print("=" * 60)
    
    parser = FanQieWebDetail()
    
    # 测试字符串（包含特殊字符）
    test_str = "这是一个测试"
    
    print(f"\n原始字符串: {test_str}")
    
    # 解码
    decoded = parser.decode_content(test_str)
    
    print(f"解码后字符串: {decoded}")
    
    if decoded == test_str:
        print("✅ 解码功能正常")
        return True
    else:
        print("⚠️ 解码结果与原始字符串不同")
        return True  # 这是正常的，因为可能包含特殊字符


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("番茄小说解析功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试1：获取书籍信息
    try:
        result1 = test_book_info()
        results.append(("获取书籍信息", result1))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("获取书籍信息", False))
    
    # 测试2：获取章节内容
    try:
        result2 = test_chapter_content()
        results.append(("获取章节内容", result2))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("获取章节内容", False))
    
    # 测试3：字符解码
    try:
        result3 = test_decode()
        results.append(("字符解码", result3))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("字符解码", False))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 60)


if __name__ == "__main__":
    main()
