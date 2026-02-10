"""
测试 BeautifulSoup 是否正常工作
"""

try:
    from bs4 import BeautifulSoup
    print("✅ BeautifulSoup 已安装")
    
    # 测试解析
    html = "<html><body><h1>测试</h1></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.select_one('h1')
    
    if h1 and h1.get_text() == "测试":
        print("✅ BeautifulSoup 解析功能正常")
    else:
        print("❌ BeautifulSoup 解析功能异常")
        
except ImportError:
    print("❌ BeautifulSoup 未安装")
    print("请运行: pip install beautifulsoup4")
except Exception as e:
    print(f"❌ 测试失败: {e}")
