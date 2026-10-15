import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent
PAYLOAD_FILE = ROOT / "payload.json"
# 读取本地保存的浏览器中“搜索”时发送的完整请求体
payload = json.loads(
    PAYLOAD_FILE.read_text(encoding="utf-8")
)

# 向搜索接口发送 POST 请求，把完整请求体交给服务器处理
response = requests.post(
    "https://open.mit.edu/api/v0/search/",
    json=payload,
    timeout=30
)
response.raise_for_status()
data = response.json()


for hit in data["hits"]["hits"]:
    course = hit["_source"]
    print(course["title"])
    print("; ".join(course.get("topics") or []))