"""项目一：襄阳市人社局“招录招聘”公告采集参考答案。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

import time

import pandas as pd
import requests
from lxml import etree


# ============================================================
# 1. 集中配置
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
BASE_URL = "http://rsj.xiangyang.gov.cn/xwzx/zlzp/"

# 正式采集前 30 页；调试时可临时改为 1。
MAX_PAGES = 30
INTERVAL = 2
TIMEOUT = 20
ENCODING = "utf-8"

# 使用固定目录，重新运行时更新同一组结果文件。
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT = BASE_DIR / "data" / "output" / "announcements.csv"
FAILURES_FILE = BASE_DIR / "logs" / "failed_pages.csv"
SUMMARY_FILE = BASE_DIR / "logs" / "run_summary.txt"

COLUMNS = [
    "title",
    "publish_date",
    "detail_url",
    "source_url",
    "page",
    "collected_at",
]


def now():
    """教师提供：返回带 UTC+08:00 时区的采集时间。"""
    china_time = timezone(timedelta(hours=8))
    return datetime.now(china_time).isoformat(timespec="seconds")


# ============================================================
# 2. build_url
# ============================================================

def build_url(page):
    """根据从 1 开始的逻辑页码，返回当前列表页 URL。"""

    if page < 1:
        raise ValueError("页码必须从 1 开始")

    if page == 1:
        return BASE_URL

    return urljoin(BASE_URL, f"index_{page - 1}.shtml")


# ============================================================
# 3. fetch_page
# ============================================================

def fetch_page(url, page):
    """请求一页，保存原始 HTML，并返回解码后的 HTML 字符串。"""

    raw_path = RAW_DIR / f"page_{page}.html"

    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(response.content)

    return response.content.decode(ENCODING)


# ============================================================
# 4. parse_page
# ============================================================

def parse_page(text, page_url, page, collected_at):
    """解析一页 HTML，返回由公告字典组成的列表。"""

    tree = etree.HTML(text)
    if tree is None:
        raise ValueError("无法解析 HTML")

    # 一页公告分布在多个 ul.news-list 中，因此直接选择所有公告 li。
    items = tree.xpath(
        '//ul[contains(concat(" ", normalize-space(@class), " "), '
        '" news-list ")]/li'
    )
    if not items:
        raise ValueError("公告列表为空，需要人工检查网页结构")

    records = []

    for item in items:
        links = item.xpath("./a[@href]")
        if len(links) != 1:
            raise ValueError("公告链接数量不符合预期")

        link = links[0]
        title = (link.get("title") or "").strip()
        href = (link.get("href") or "").strip()
        date_text = item.xpath("string(./time)").strip()

        if not title or not href:
            raise ValueError("公告标题或链接缺失")

        if date_text:
            try:
                publish_date = datetime.strptime(
                    date_text, "%Y-%m-%d"
                ).strftime("%Y-%m-%d")
            except ValueError as exc:
                raise ValueError(f"公告日期格式异常：{date_text}") from exc
        else:
            publish_date = ""
            print(f"[WARN] 第 {page} 页有一条公告缺少日期：{title}")

        records.append(
            {
                "title": title,
                "publish_date": publish_date,
                "detail_url": urljoin(page_url, href),
                "source_url": page_url,
                "page": page,
                "collected_at": collected_at,
            }
        )

    return records


# ============================================================
# 5. save_csv
# ============================================================

def save_csv(records, path, columns):
    """将 list[dict] 按指定列保存为 CSV。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame(records, columns=columns)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


# ============================================================
# 6. 教师提供：保存简要运行说明
# ============================================================

def save_summary(completed_pages, record_count, failures):
    """保存最基本的运行结果，不要求学生编写日志系统。"""
    status = "incomplete" if failures else "scope_complete"
    reason = failures[0]["reason"] if failures else "指定页数范围已完成"

    text = (
        f"采集时间：{now()}\n"
        f"计划页数：{MAX_PAGES}\n"
        f"成功页码：{completed_pages}\n"
        f"公告条数：{record_count}\n"
        f"状态：{status}\n"
        f"说明：{reason}\n"
    )

    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(text, encoding="utf-8")


# ============================================================
# 7. main
# ============================================================

def main():
    """程序主入口。"""
    all_records = []
    failures = []
    completed_pages = []

    for page in range(1, MAX_PAGES + 1):
        if page > 1:
            time.sleep(INTERVAL)

        url = build_url(page)
        print(f"[INFO] 第 {page} 页：{url}")

        try:
            text = fetch_page(url, page)
            records = parse_page(text, url, page, now())
            all_records.extend(records)

        except (requests.RequestException, ValueError, OSError) as exc:
            failures.append({"page": page, "url": url, "reason": str(exc)})
            print(f"[ERROR] 第 {page} 页失败：{exc}")
            print("[ERROR] 停止本次采集，不能把失败当作末页")
            break

        completed_pages.append(page)
        print(f"[INFO] 本页 {len(records)} 条，累计 {len(all_records)} 条")

    save_csv(all_records, OUTPUT, COLUMNS)
    save_csv(failures, FAILURES_FILE, ["page", "url", "reason"])

    # 教师已经提供简要摘要，无需学生实现复杂日志。
    save_summary(completed_pages, len(all_records), failures)

    print(f"[INFO] 共采集 {len(all_records)} 条公告")
    print(f"[INFO] 公告数据：{OUTPUT}")
    print(f"[INFO] 运行说明：{SUMMARY_FILE}")


if __name__ == "__main__":
    main()
