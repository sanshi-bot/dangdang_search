"""
番茄小说详情页解析工具
使用 BeautifulSoup 解析 HTML
"""

import requests
from bs4 import BeautifulSoup


class FanQieWebDetail:
    """番茄小说详情页解析类"""
    
    # 字符映射字典（用于解码番茄小说的特殊字符）
    CHAR_MAP = {
        '58670': '0', '58413': '1', '58678': '2', '58371': '3', '58353': '4',
        '58480': '5', '58359': '6', '58449': '7', '58540': '8', '58692': '9',
        '58712': 'a', '58542': 'b', '58575': 'c', '58626': 'd', '58691': 'e',
        '58561': 'f', '58362': 'g', '58619': 'h', '58430': 'i', '58531': 'j',
        '58588': 'k', '58440': 'l', '58681': 'm', '58631': 'n', '58376': 'o',
        '58429': 'p', '58555': 'q', '58498': 'r', '58518': 's', '58453': 't',
        '58397': 'u', '58356': 'v', '58435': 'w', '58514': 'x', '58482': 'y',
        '58529': 'z', '58515': 'A', '58688': 'B', '58709': 'C', '58344': 'D',
        '58656': 'E', '58381': 'F', '58576': 'G', '58516': 'H', '58463': 'I',
        '58649': 'J', '58571': 'K', '58558': 'L', '58433': 'M', '58517': 'N',
        '58387': 'O', '58687': 'P', '58537': 'Q', '58541': 'R', '58458': 'S',
        '58390': 'T', '58466': 'U', '58386': 'V', '58697': 'W', '58519': 'X',
        '58511': 'Y', '58634': 'Z', '58611': '的', '58590': '一', '58398': '是',
        '58422': '了', '58657': '我', '58666': '不', '58562': '人', '58345': '在',
        '58510': '他', '58496': '有', '58654': '这', '58441': '个', '58493': '上',
        '58714': '们', '58618': '来', '58528': '到', '58620': '时', '58403': '大',
        '58461': '地', '58481': '为', '58700': '子', '58708': '中', '58503': '你',
        '58442': '说', '58639': '生', '58506': '国', '58663': '年', '58436': '着',
        '58563': '就', '58391': '那', '58357': '和', '58354': '要', '58695': '她',
        '58372': '出', '58696': '也', '58551': '得', '58445': '里', '58408': '后',
        '58599': '自', '58424': '以', '58394': '会', '58348': '家', '58426': '可',
        '58673': '下', '58417': '而', '58556': '过', '58603': '天', '58565': '去',
        '58604': '能', '58522': '对', '58632': '小', '58622': '多', '58350': '然',
        '58605': '于', '58617': '心', '58401': '学', '58637': '么', '58684': '之',
        '58382': '都', '58464': '好', '58487': '看', '58693': '起', '58608': '发',
        '58392': '当', '58474': '没', '58601': '成', '58355': '只', '58573': '如',
        '58499': '事', '58469': '把', '58361': '还', '58698': '用', '58489': '第',
        '58711': '样', '58457': '道', '58635': '想', '58492': '作', '58647': '种',
        '58623': '开', '58521': '美', '58609': '总', '58530': '从', '58665': '无',
        '58652': '情', '58676': '己', '58456': '面', '58581': '最', '58509': '女',
        '58488': '但', '58363': '现', '58685': '前', '58396': '些', '58523': '所',
        '58471': '同', '58485': '日', '58613': '手', '58533': '又', '58589': '行',
        '58527': '意', '58593': '动', '58699': '方', '58707': '期', '58414': '它',
        '58596': '头', '58570': '经', '58660': '长', '58364': '儿', '58526': '回',
        '58501': '位', '58638': '分', '58404': '爱', '58677': '老', '58535': '因',
        '58629': '很', '58577': '给', '58606': '名', '58497': '法', '58662': '间',
        '58479': '斯', '58532': '知', '58380': '世', '58385': '什', '58405': '两',
        '58644': '次', '58578': '使', '58505': '身', '58564': '者', '58412': '被',
        '58686': '高', '58624': '已', '58667': '亲', '58607': '其', '58616': '进',
        '58368': '此', '58427': '话', '58423': '常', '58633': '与', '58525': '活',
        '58543': '正', '58418': '感', '58597': '见', '58683': '明', '58507': '问',
        '58621': '力', '58703': '理', '58438': '尔', '58536': '点', '58384': '文',
        '58484': '几', '58539': '定', '58554': '本', '58421': '公', '58347': '特',
        '58569': '做', '58710': '外', '58574': '孩', '58375': '相', '58645': '西',
        '58592': '果', '58572': '走', '58388': '将', '58370': '月', '58399': '十',
        '58651': '实', '58546': '向', '58504': '声', '58419': '车', '58407': '全',
        '58672': '信', '58675': '重', '58538': '三', '58465': '机', '58374': '工',
        '58579': '物', '58402': '气', '58702': '每', '58553': '并', '58360': '别',
        '58389': '真', '58560': '打', '58690': '太', '58473': '新', '58512': '比',
        '58653': '才', '58704': '便', '58545': '夫', '58641': '再', '58475': '书',
        '58583': '部', '58472': '水', '58478': '像', '58664': '眼', '58586': '等',
        '58568': '体', '58674': '却', '58490': '加', '58476': '电', '58346': '主',
        '58630': '界', '58595': '门', '58502': '利', '58713': '海', '58587': '受',
        '58548': '听', '58351': '表', '58547': '德', '58443': '少', '58460': '克',
        '58636': '代', '58585': '员', '58625': '许', '58694': '稜', '58428': '先',
        '58640': '口', '58628': '由', '58612': '死', '58446': '安', '58468': '写',
        '58410': '性', '58508': '马', '58594': '光', '58483': '白', '58544': '或',
        '58495': '住', '58450': '难', '58643': '望', '58486': '教', '58406': '命',
        '58447': '花', '58669': '结', '58415': '乐', '58444': '色', '58549': '更',
        '58494': '拉', '58409': '东', '58658': '神', '58557': '记', '58602': '处',
        '58559': '让', '58610': '母', '58513': '父', '58500': '应', '58378': '直',
        '58680': '字', '58352': '场', '58383': '平', '58454': '报', '58671': '友',
        '58668': '关', '58452': '放', '58627': '至', '58400': '张', '58455': '认',
        '58416': '接', '58552': '告', '58614': '入', '58582': '笑', '58534': '内',
        '58701': '英', '58349': '军', '58491': '候', '58467': '民', '58365': '岁',
        '58598': '往', '58425': '何', '58462': '度', '58420': '山', '58661': '觉',
        '58615': '路', '58648': '带', '58470': '万', '58377': '男', '58520': '边',
        '58646': '风', '58600': '解', '58431': '叫', '58715': '任', '58524': '金',
        '58439': '快', '58566': '原', '58477': '吃', '58642': '妈', '58437': '变',
        '58411': '通', '58451': '师', '58395': '立', '58369': '象', '58706': '数',
        '58705': '四', '58379': '失', '58567': '满', '58373': '战', '58448': '远',
        '58659': '格', '58434': '士', '58679': '音', '58432': '轻', '58689': '目',
        '58591': '条', '58682': '呢'
    }
    
    def __init__(self, headers=None):
        """
        初始化
        :param headers: 请求头
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
    
    def decode_content(self, content):
        """
        解码番茄小说的特殊字符
        :param content: 原始内容
        :return: 解码后的内容
        """
        decoded = []
        for char in content:
            char_code = str(ord(char))
            if char_code in self.CHAR_MAP:
                decoded.append(self.CHAR_MAP[char_code])
            else:
                decoded.append(char)
        return ''.join(decoded)
    
    def get_book_info(self, url):
        """
        获取书籍基本信息
        :param url: 书籍详情页URL
        :return: 书籍信息字典
        """
        try:
            response = requests.get(url=url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            html = response.text
            
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # 书名
            name_tag = soup.select_one('.info-name h1')
            name = name_tag.get_text(strip=True) if name_tag else ''
            
            # 作者
            author_tag = soup.select_one('.author-name-text')
            author = author_tag.get_text(strip=True) if author_tag else ''
            
            # 标签信息
            label_tags = soup.select('.info-label span')
            labels = [tag.get_text(strip=True) for tag in label_tags]
            
            # 章节列表
            chapter_tags = soup.select('.chapter-item-title')
            chapters = []
            for tag in chapter_tags:
                chapter_title = tag.get_text(strip=True)
                chapter_href = tag.get('href', '')
                if chapter_href:
                    chapters.append({
                        'title': chapter_title,
                        'url': 'https://fanqienovel.com' + chapter_href
                    })
            
            return {
                'name': name,
                'author': author,
                'labels': labels,
                'chapters': chapters
            }
        
        except Exception as e:
            print(f"获取书籍信息失败: {e}")
            return None
    
    def get_chapter_content(self, chapter_url):
        """
        获取章节内容
        :param chapter_url: 章节URL
        :return: 解码后的章节内容
        """
        try:
            response = requests.get(url=chapter_url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            html = response.text
            
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取小说内容
            content_tags = soup.select('.muye-reader-content-16 p')
            content_list = [tag.get_text(strip=True) for tag in content_tags]
            
            # 合并内容
            raw_content = '\n'.join(content_list)
            
            # 解码内容
            decoded_content = self.decode_content(raw_content)
            
            return decoded_content
        
        except Exception as e:
            print(f"获取章节内容失败: {e}")
            return None
    
    def download_book(self, book_url, save_path=None):
        """
        下载整本书
        :param book_url: 书籍详情页URL
        :param save_path: 保存路径（可选）
        :return: 是否成功
        """
        # 获取书籍信息
        book_info = self.get_book_info(book_url)
        if not book_info:
            print("获取书籍信息失败")
            return False
        
        print(f"书名: {book_info['name']}")
        print(f"作者: {book_info['author']}")
        print(f"标签: {', '.join(book_info['labels'])}")
        print(f"章节数: {len(book_info['chapters'])}")
        print("-" * 50)
        
        # 如果没有指定保存路径，使用书名作为文件名
        if not save_path:
            save_path = f"{book_info['name']}.txt"
        
        # 下载所有章节
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"书名: {book_info['name']}\n")
            f.write(f"作者: {book_info['author']}\n")
            f.write(f"标签: {', '.join(book_info['labels'])}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, chapter in enumerate(book_info['chapters'], 1):
                print(f"正在下载第 {i}/{len(book_info['chapters'])} 章: {chapter['title']}")
                
                content = self.get_chapter_content(chapter['url'])
                if content:
                    f.write(f"\n\n{'=' * 50}\n")
                    f.write(f"第 {i} 章: {chapter['title']}\n")
                    f.write(f"{'=' * 50}\n\n")
                    f.write(content)
                else:
                    print(f"  下载失败: {chapter['title']}")
        
        print(f"\n下载完成！保存到: {save_path}")
        return True


def main():
    """主函数 - 示例用法"""
    # 创建解析器实例
    parser = FanQieWebDetail()
    
    # 示例：获取书籍信息
    book_url = "https://fanqienovel.com/page/7276384138653862966"
    
    print("=" * 50)
    print("番茄小说详情页解析工具")
    print("=" * 50)
    print()
    
    # 获取书籍信息
    book_info = parser.get_book_info(book_url)
    if book_info:
        print(f"书名: {book_info['name']}")
        print(f"作者: {book_info['author']}")
        print(f"标签: {', '.join(book_info['labels'])}")
        print(f"章节数: {len(book_info['chapters'])}")
        print()
        
        # 显示前5章
        print("前5章:")
        for i, chapter in enumerate(book_info['chapters'][:5], 1):
            print(f"  {i}. {chapter['title']}")
        print()
        
        # 询问是否下载
        choice = input("是否下载整本书？(y/n): ").strip().lower()
        if choice == 'y':
            parser.download_book(book_url)


if __name__ == "__main__":
    main()
