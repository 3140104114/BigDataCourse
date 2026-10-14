from bs4 import BeautifulSoup
from pathlib import Path
import requests
import re
from urllib.parse import urljoin
import pandas as pd
from pathlib import Path

URL = "https://jyj.wuhan.gov.cn/zwdt/tsgg/index.shtml"

# # 读取本地备份 HTML
# RAW_PATH = Path("data/raw/wuhan_tsgg_index.html")
# html = RAW_PATH.read_text(encoding="utf-8")

response = requests.get(URL, timeout=10)
response.raise_for_status()
response.encoding = response.apparent_encoding

html = response.text

soup = BeautifulSoup(html, "html.parser")

# 实践2：提取所有链接
links = soup.select("a")
print("链接数量：", len(links))

for a in links[:10]:
    print(a.get_text(" ", strip=True), a.get("href"))




# 实践3：筛选公告条目
pattern = re.compile(r"(.+?)\s*时间：(\d{4}-\d{2}-\d{2})")
records = []

for a in soup.select("a"):
    text = a.get_text(" ", strip=True)
    m = pattern.search(text)
    if not m:
        continue
    title = m.group(1).strip()
    date = m.group(2)
    records.append({"title": title, "date": date, "href": a.get("href")})
    # print({"title": title, "date": date, "href": a.get("href")})



# 补全详情链接,整理为字典列表
for item in records:
    item["url"] = urljoin(URL, item.pop("href"))
    item["source_page"] = URL

# print(records[:3])


# 保存成csv
OUT_PATH = Path("output/wuhan_announcements_week03.csv")

df = pd.DataFrame(records)
df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

print(df.head())
print("保存成功：", OUT_PATH)