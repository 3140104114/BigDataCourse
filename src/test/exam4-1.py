import requests
from lxml import etree
import time
import pandas as pd
import sqlite3

all_jobs = []

base_url = "https://jyj.wuhan.gov.cn/zwdt/tsgg/index_{}.shtml"

for page in range(1, 7):

    if page == 1:
        url = "https://jyj.wuhan.gov.cn/zwdt/tsgg/index.shtml"
    else:
        url = base_url.format(page-1)

    resp = requests.get(url)
    resp.encoding = resp.apparent_encoding # 根据网页特征推测更可能的编码
    html = etree.HTML(resp.text) # 返回 lxml 节点对象

    titles = html.xpath('//h2/text()') # 浏览器定位标题标签

    for t in titles:
        all_jobs.append(
            {
                "title": t.strip(),
                "page": page
            }
        )

    time.sleep(1)

# print(all_jobs[:11])
# print(f"共采集 {len(all_jobs)} 条")


# 存到CSV
# df = pd.DataFrame(all_jobs)
# df.to_csv(
#     "output/jobs.csv",
#     encoding="utf-8-sig",
#     index=False
# )

# print(df.head()) # 看前 5 行对不对




# 连接数据库，存到SQLite
conn = sqlite3.connect("education.db")

cur = conn.cursor() # cursor 游标对象，执行SQL语句的对象

# 创建数据表，字段 title 和 page 分别存储标题和页码，来自前面的字典 key
cur.execute("""
CREATE TABLE IF NOT EXISTS jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    page INTEGER
)
""")

# 批量插入，python 字典转换为 SQL
# 数据库不会自动读取我们的 all_jobs。它不知道列表里面有哪些数据，也不知道字典中的 key 对应哪个字段。
# 所以我们需要增加一个转换步骤：前面爬虫得到的是 Python 数据结构 字典
# 数据库需要的是一条记录 字段
# 因此我们通过 for 循环遍历 all_jobs，每循环一次，就执行一次 INSERT，把一个字典转换成数据库中的一行记录。
for job in all_jobs:

    cur.execute(
        """
        INSERT INTO jobs(title, page)
        VALUES (?, ?)
        """,
        (
            job["title"],
            job["page"]
        )
    )

conn.commit() # 循环插入，一次提交

# 查询验证
cur.execute(
    "SELECT * FROM jobs"
)

results = cur.fetchall()

for row in results:
    print(row)