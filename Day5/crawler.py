# crawler.py
# ------------------------------------------------------------
# 第5次课：函数重构版公告采集器
#
# 主要函数：
#
# build_url()
#     根据页码生成列表页地址
#
# fetch_page()
#     获取一页 HTML
#
# parse_page()
#     把 HTML 解析成结构化记录
#
# save_csv()
#     把记录保存为 CSV
#
# crawl()
#     调度多页任务
#
# main()
#     组织整个程序
# ------------------------------------------------------------


# ---------- 1. 导入 ----------

from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

import json
import re
import time

import requests
import pandas as pd
from lxml import etree

import sqlite3


# ============================================================
# 2. 集中配置
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

BASE_URL = "https://jyj.wuhan.gov.cn/zwdt/tsgg/"

MAX_PAGES = 3

INTERVAL = 2

TIMEOUT = 20

ENCODING = "utf-8"

# online / offline
MODE = "online"

RAW_DIR = (BASE_DIR/"data"/"raw")

OUTPUT = (BASE_DIR/"data"/"notices.csv")

FAILURES_FILE = (BASE_DIR/"logs"/"failed_pages.csv")

SUMMARY_FILE = (BASE_DIR/"logs"/"run_summary.json")

COLUMNS = [
    "title",
    "date",
    "url",
    "page",
    "source_url"
]


# ============================================================
# 3. build_url
# ============================================================

def build_url(page):
    """
    根据页码生成当前列表页 URL。

    参数
    ----------
    page : int
        人看到的页码，从 1 开始。

    返回
    ----------
    str
        当前页完整 URL。
    """

    if page == 1:
        filename = "index.shtml"
    else:
        filename = (f"index_{page - 1}.shtml")

    return urljoin(BASE_URL,filename)


# ============================================================
# 4. fetch_page
# ============================================================

def fetch_page(url, page, mode):
    """
    获取一页网页文本。

    online：
        请求真实网页，
        同时保存原始 HTML 字节。

    offline：
        读取之前保存的真实 HTML 快照。

    两种模式最终都返回同一种数据：
        HTML 字符串。
    """

    raw_path = (RAW_DIR/f"page_{page}.html")

    # ---------- 离线模式 ----------
    if mode == "offline":
        return raw_path.read_text(encoding=ENCODING)

    # ---------- 在线模式 ----------
    response = requests.get(url,timeout=TIMEOUT)

    # 如果出现 404、403、500 等错误，
    # 直接抛出异常
    response.raise_for_status()

    # 保存服务器返回的原始字节
    RAW_DIR.mkdir(parents=True,exist_ok=True)
    raw_path.write_bytes(response.content)

    # 将 bytes 按网页实际编码解码成 str
    text = response.content.decode(ENCODING)

    return text


# ============================================================
# 5. parse_page
# ============================================================

def parse_page(text, page_url, page):
    """
    把一页 HTML 字符串解析成公告记录。

    输入
    ----------
    text
        HTML 字符串

    page_url
        当前列表页 URL

    page
        当前页码

    输出
    ----------
    list[dict]
        每个字典表示一条公告
    """

    # ---------- HTML → DOM ----------
    tree = etree.HTML(text)
    if tree is None:
        raise ValueError("无法解析 HTML")

    # ---------- 找公告列表容器 ----------
    containers = tree.xpath('//ul[@class="item-box"]')
    if len(containers) != 1:
        raise ValueError("公告列表容器数量不符合预期")

    # ---------- 找公告 li ----------
    items = containers[0].xpath("./li")
    if not items:
        raise ValueError("公告列表为空，需要人工确认")

    # 当前页结果
    records = []

    # ---------- 逐条抽字段 ----------

    for item in items:

        links = item.xpath('./a[@class="item-li-a"]')

        if len(links) != 1:
            raise ValueError("公告链接数量不符合预期")

        link = links[0]

        # 标题
        title = link.xpath("string(./h2)").strip()

        # 相对链接
        href = link.get("href")

        # 日期原文本
        date_text = link.xpath('string(./div[@class="other"])').strip()

        # 提取 YYYY-MM-DD
        match = re.search(r"\d{4}-\d{2}-\d{2}", date_text)

        # 关键字段检查
        if (not title or not href or match is None):
            raise ValueError("标题、链接或日期缺失")

        # 当前公告详情页 URL
        detail_url = urljoin(page_url, href)

        records.append(
            {
                "title": title,
                "date": match.group(0),
                "url": detail_url,
                "page": page,
                "source_url": page_url
            }
        )


    # 注意：
    # return 一定放在 for 循环外
    return records


# ============================================================
# 6. save_csv
# ============================================================

def save_csv(records, path, columns):
    """
    将 list[dict] 保存为 CSV。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records, columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")



# ============================================================
# 6.1 save_sqlite
# ============================================================

def save_sqlite(records, path, columns):
    """
    将相同的 records 保存到 SQLite。

    注意：
    fetch_page 和 parse_page
    完全不需要修改。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records, columns=columns)
    conn = sqlite3.connect(path)

    try:
        df.to_sql("notices", conn, if_exists="replace", index=False)
    finally:
        conn.close()


# ============================================================
# 7. crawl
# ============================================================

def crawl(max_pages, interval, mode):
    """
    调度整个多页采集任务。

    返回：
    1. 所有成功获取的记录
    2. 失败页
    3. 成功完成的页码
    """

    # ---------- 配置检查 ----------

    if mode not in ("online", "offline"):
        raise ValueError("MODE 只能是 online 或 offline")

    if max_pages < 1:
        raise ValueError("页数至少为 1")

    if interval < 0:
        raise ValueError("等待时间不能为负数")

    all_records = []
    failures = []
    completed_pages = []


    # ---------- 多页循环 ----------

    for page in range(1, max_pages + 1):

        # 在线时避免连续快速请求
        if (mode == "online" and page > 1):
            time.sleep(interval)

        # 当前页 URL
        url = build_url(page)
        print(f"[INFO] 第 {page} 页：{url}")

        try:
            # 获取
            text = fetch_page(url, page, mode)

            # 解析
            records = parse_page(text,url,page)

        except (
            requests.RequestException,
            ValueError,
            OSError
        ) as exc:

            failures.append(
                {
                    "page": page,
                    "url": url,
                    "reason": str(exc)
                }
            )

            print(f"[ERROR] {exc}")
            print("[ERROR] 停止本次采集")

            # 本课采用出错即停
            break


        # 当前页成功后才加入总列表
        all_records.extend(records)
        completed_pages.append(page)

        print(f"[INFO] 本页 {len(records)} 条，" f"累计 {len(all_records)} 条")


    return (all_records, failures,completed_pages)


# ============================================================
# 8. main
# ============================================================

def main():
    """
    程序主入口。
    """

    # 记录本次任务开始时间
    started_at = (datetime.now().isoformat(timespec="seconds"))


    # ---------- 执行采集 ----------

    records, failures, completed = crawl(MAX_PAGES, INTERVAL, MODE)


    # ---------- 保存数据 ----------

    save_csv(records, OUTPUT, COLUMNS)

    # save_sqlite(records, BASE_DIR/ "data"/ "education.db", COLUMNS) 


    # ---------- 保存失败页 ----------

    save_csv(failures, FAILURES_FILE,
        [
            "page",
            "url",
            "reason"
        ]
    )


    # ---------- 生成运行摘要 ----------

    summary = {

        "started_at": started_at,
        "mode": MODE,
        "source": BASE_URL,
        "requested_pages":
            MAX_PAGES,
        "completed_pages":
            completed,
        "record_count":
            len(records),
        "status":
            (
                "incomplete"
                if failures
                else "scope_complete"
            )
    }


    # ---------- 保存 JSON 摘要 ----------

    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)

    SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    # ---------- 输出运行情况 ----------

    print(f"[INFO] 已保存 " f"{len(records)} 条：" f"{OUTPUT}")

    if failures:
        print("[WARN] 结果不完整，请检查失败页和运行摘要")

    else:
        print("[INFO] 指定页数范围已完成，不代表采集完整网站")


# ============================================================
# 9. 程序入口
# ============================================================

if __name__ == "__main__":
    main()