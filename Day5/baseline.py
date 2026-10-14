# baseline.py
# ------------------------------------------------------------
# 第5次课重构前的基准版本
#
# 特点：
# 1. 所有采集逻辑按执行顺序写在一个文件里
# 2. 没有把请求、解析、保存封装成函数
# 3. 可以在线访问真实网页，也可以读取本地 HTML 快照
# 4. 后面会把它重构为 crawler.py
#
# 重要：
# baseline.py 和 crawler.py 要保持：
# - 相同输入
# - 相同采集范围
# - 相同字段
# - 相同记录顺序
#
# 这样才能判断“重构有没有改变结果”
# ------------------------------------------------------------


# ---------- 1. 导入需要的库 ----------

from pathlib import Path
from urllib.parse import urljoin

import re
import time

import requests
import pandas as pd
from lxml import etree


# ---------- 2. 设置本次任务需要的参数 ----------

# 当前脚本所在的文件夹
BASE_DIR = Path(__file__).resolve().parent

# 武汉市教育局“通知公告”栏目
BASE_URL = "https://jyj.wuhan.gov.cn/zwdt/tsgg/"

# 本次课堂只采前 3 页
MAX_PAGES = 3

# 相邻网络请求之间等待 2 秒
INTERVAL = 2

# 请求最长等待时间
TIMEOUT = 20

# 本案例已经核验网页编码为 UTF-8
ENCODING = "utf-8"

# online：访问真实网页
# offline：读取 data/raw 中已经保存的真实 HTML
MODE = "online"

# 原始网页快照保存位置
RAW_DIR = BASE_DIR/"data"/"raw"

# CSV 输出位置
OUTPUT = BASE_DIR/"data"/"baseline.csv"

# 最终 CSV 的字段顺序
COLUMNS = [
    "title",
    "date",
    "url",
    "page",
    "source_url"
]


# ---------- 3. 创建保存所有公告的列表 ----------

all_records = []


# ---------- 4. 循环处理每一页 ----------

for page in range(1, MAX_PAGES + 1):

    # ----------------------------------------
    # 4.1 根据页码生成当前页 URL
    # ----------------------------------------

    # 第一页：
    # index.shtml
    #
    # 第二页：
    # index_1.shtml
    #
    # 第三页：
    # index_2.shtml

    if page == 1:
        filename = "index.shtml"
    else:
        filename = f"index_{page - 1}.shtml"

    page_url = urljoin(BASE_URL, filename)

    print(f"[INFO] 正在处理第 {page} 页：{page_url}")


    # ----------------------------------------
    # 4.2 在线获取网页 / 离线读取网页快照
    # ----------------------------------------

    raw_path = RAW_DIR / f"page_{page}.html"

    if MODE == "online":

        # 从第 2 页开始，在发送请求之前等待
        if page > 1:
            time.sleep(INTERVAL)

        # 发出 HTTP GET 请求
        response = requests.get(page_url, timeout=TIMEOUT)

        # 如果服务器返回 4xx / 5xx，
        # 直接抛出异常，不继续把错误页面当正常页面解析
        response.raise_for_status()

        # 保存服务器返回的原始字节
        # 这样以后可以回查，也可以用于离线复现
        RAW_DIR.mkdir(parents=True, exist_ok=True)

        raw_path.write_bytes(response.content)

        # 当前案例已经确认网页是 UTF-8
        # 把原始 bytes 解码成字符串
        text = response.content.decode(ENCODING)

    else:

        # offline 模式不访问网站
        # 直接读取之前保存的真实 HTML 快照
        text = raw_path.read_text(encoding=ENCODING)


    # ----------------------------------------
    # 4.3 把 HTML 字符串解析成 DOM 树
    # ----------------------------------------

    tree = etree.HTML(text)
    if tree is None:
        raise ValueError(f"第 {page} 页 HTML 无法解析")


    # ----------------------------------------
    # 4.4 找到公告列表容器
    # ----------------------------------------

    containers = tree.xpath('//ul[@class="item-box"]')
    # 本案例中应该只有一个公告列表容器
    if len(containers) != 1:
        raise ValueError(f"第 {page} 页公告列表容器数量异常：" f"{len(containers)}")

    container = containers[0]


    # ----------------------------------------
    # 4.5 找到这一页中的所有公告 li
    # ----------------------------------------

    items = container.xpath("./li")
    if not items:
        raise ValueError(f"第 {page} 页公告列表为空，需要人工确认")


    # ----------------------------------------
    # 4.6 从每一条公告中抽取字段，即先确定“一条公告”，再从这一条公告内部取标题、日期、链接
    # ----------------------------------------

    for item in items:

        # 找当前 li 中的公告链接
        links = item.xpath('./a[@class="item-li-a"]')

        if len(links) != 1:
            raise ValueError(f"第 {page} 页存在公告链接数量异常")

        link = links[0]

        # 标题
        title = link.xpath("string(./h2)").strip()

        # 相对链接
        href = link.get("href")

        # 日期区域，例如：
        # 时间：2026-09-21
        date_text = link.xpath('string(./div[@class="other"])').strip()

        # 从日期文本中提取 YYYY-MM-DD
        match = re.search(r"\d{4}-\d{2}-\d{2}", date_text)

        # 任一关键字段缺失，都停止检查
        if (not title or not href or match is None):
            raise ValueError(f"第 {page} 页存在标题、链接或日期缺失")

        # 把相对链接转换成完整 URL
        detail_url = urljoin(page_url, href)

        # 一条公告对应一个字典
        record = {
            "title": title,
            "date": match.group(0),
            "url": detail_url,
            "page": page,
            "source_url": page_url
        }

        # append：加入一条公告
        all_records.append(record)

    print(f"[INFO] 第 {page} 页 {len(items)} 条，" f"累计 {len(all_records)} 条")


# ---------- 5. 保存 CSV ----------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(all_records, columns=COLUMNS)

df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print(f"[INFO] 共采集 {len(all_records)} 条")
print(f"[INFO] 已保存：{OUTPUT}")
print(df.head())