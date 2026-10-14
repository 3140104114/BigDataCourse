from pathlib import Path
import requests

URL = "https://jyj.wuhan.gov.cn/zwdt/tsgg/index.shtml"
RAW_PATH = Path("data/raw/wuhan_tsgg_index.html")

response = requests.get(URL, timeout=10)
response.encoding = response.apparent_encoding
RAW_PATH.write_text(response.text, encoding="utf-8")