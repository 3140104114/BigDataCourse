# verify_parse.py
# ------------------------------------------------------------
# 单独验证：
# build_url → fetch_page → parse_page
#
# 不执行整个多页采集任务
# ------------------------------------------------------------


from crawler import (build_url, fetch_page, parse_page)


# ---------- 1. 生成第一页 URL ----------

url = build_url(1)
print("第一页 URL：", url)


# ---------- 2. 从本地真实快照读取 ----------

text = fetch_page(url, 1, "offline")


# ---------- 3. 解析第一页 ----------

records = parse_page(text, url, 1)


# ---------- 4. 验证 ----------

print("本页记录数：", len(records))
print("第一条记录：")
print(records[0])