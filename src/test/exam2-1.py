import requests

url = "https://jyj.wuhan.gov.cn/zwdt/tsgg/index.shtml"
headers = {"User-Agent": "BigDataCourse/1.0"}

try:
    response = requests.get(
        url, headers=headers, timeout=10
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    print("状态码：", response.status_code)
    print("返回内容：", response.text[:2000])
    print("编码：", response.encoding)

except requests.RequestException as e:
    print("请求失败：", e)