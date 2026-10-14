import requests

# print(requests.__version__)

url = "https://example.com"

response = requests.get(url)

print(response)

# print("状态码：", response.status_code)
# print("返回内容：", response.text[:1000])
print("编码：", response.encoding)