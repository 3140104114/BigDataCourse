import requests
from bs4 import BeautifulSoup

url = "https://jyj.wuhan.gov.cn/zwdt/tsgg/index.shtml"
response = requests.get(url, timeout=10)
response.encoding = response.apparent_encoding

print("【response】  ", response.text[:2000])

soup = BeautifulSoup(response.text, "html.parser")
print("【soup title】  ", soup.title)


