# verify_results.py
# ------------------------------------------------------------
# 验证 baseline.py 与 crawler.py
# 在相同 HTML 快照下是否得到完全一致的结果
# ------------------------------------------------------------


from pathlib import Path
import pandas as pd


BASE_DIR = (Path(__file__).resolve().parent)

# ---------- 读取两份结果 ----------

before = pd.read_csv(BASE_DIR/"data"/"baseline.csv")
after = pd.read_csv(BASE_DIR/"data"/"notices.csv")


# ---------- 1. 比较行列数 ----------

print("重构前：", before.shape)
print("重构后：", after.shape)


# ---------- 2. 比较完整内容 ----------

print("逐项一致：", before.equals(after))


# ---------- 3. 查看每页条数 ----------

print("\n每页记录数：")
print(after.groupby("page").size())


# ---------- 4. 检查缺失 ----------

print("\n缺失值统计：")
print(after.isna().sum())


# ---------- 5. 检查详情链接重复 ----------

print("\n重复详情链接数：", after["url"].duplicated().sum())