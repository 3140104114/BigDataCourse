# OCW 搜索 Python 的 Ajax 抓包与采集

这个练习完整对应同一任务：OCW 页面搜索 python → 找到页面POST请求 → 保存请求体 → Python复现 → 保存课程表。

## 一 在浏览器找真实请求

1. 打开 https://ocw.mit.edu/search/ 。
2. 按F12或Ctrl+Shift+I，打开Network。
3. 确认记录开启，清空旧记录，点击Fetch/XHR。
4. 在页面搜索框输入python并搜索，保持Courses课程类别；不要切换到课程文件/学习资源类别。
5. 点开名称可能为search/的候选请求，在Headers核对地址和方法。当前页面脚本核对到的地址是 https://open.mit.edu/api/v0/search/ ，方法POST。若有OPTIONS，不要把它当业务POST。
6. 在Preview/Response展开 hits → hits → 某一项 → _source，核对其中title与页面课程一致。
7. 在Payload中查看Request Payload，选择View source（或对应的原始文本显示方式），复制整个JSON对象。不同开发者工具的菜单名称可能不同。
8. 用VS Code打开本目录，将真实请求体保存/替换为payload.json，编码UTF-8。只保存JSON，不保存URL、JavaScript fetch语句或外层额外引号。

## 二 运行

在当前课程Python环境执行：

```text
python -m pip install requests
python ocw_python.py
```

脚本默认读取旁边的payload.json，每次只发一次POST请求。每个批次输出到output/run_时间戳，包含request_payload.json、response.json、courses.csv与metadata.json。直接用Excel打开courses.csv。

核心转换是：

```python
payload = json.loads(Path("payload.json").read_text(encoding="utf-8"))
response = requests.post("https://open.mit.edu/api/v0/search/", json=payload, timeout=30)
response.raise_for_status()
data = response.json()
for hit in data["hits"]["hits"]:
    course = hit["_source"]
    print(course["title"])
```

不能改成GET加q参数，不能把请求体字典作为表单提交。offered_by与topics在本响应中是字符串列表；不要套用另一个课程接口的results或offered_by.name。

## 三 核验与第二批

至少对照三条课程标题、课程号、主题及链接。course_url由第一条runs中的slug连接OCW域名得到，并非另行抓取的字段；资源有多个runs时此规则只选第一条。相同标题可能来自不同年份，不按标题去重。

先在网页加载下一批，再比较真实Payload的from和size。本包参考体为from=0、size=10；验证下一批可改为from=10。一次只改一个条件，间隔不少于2秒，不无限循环。匹配总数不等于已采到的条数。

若想换搜索词，先在网页重新搜索，再复制新请求体。复杂请求体中关键词出现多次，仅改suggest.text不等于改变课程查询。

## 四 参考请求体和真实样例的来源

payload.json是依据当前OCW页面官方脚本中的buildSearchQuery函数生成的参考体：text=python、type=course、offered_by=OCW、from=0、size=10；它不是本次浏览器录制的网络抓包。正式课堂必须用学生自己的Network记录验证。参考脚本来源 https://ocw.mit.edu/static_shared/js/www.f859c.js 和其中依赖的 https://ocw.mit.edu/static_shared/js/common.f859c.js 。这些文件名可能随版本变化。

本包已实际向上述搜索地址发出POST并验证：2026年10月16日的一次运行返回HTTP200、173条匹配、本批10条。首批包括A Gentle Introduction to Programming Using Python、Introduction to Computer Science and Programming in Python。数据会更新；结果并不要求标题都含python，因为可能匹配简介或课程材料。

sample_run目录是这次真实请求的响应、条件、CSV和元数据，用于结果对照与离线解析。网络不可用时可解析该快照，但不能把离线解析当成新的在线搜索，也不能声称已完成页面抓包。

出现403/429或其他访问限制时停止请求并检查原因。所有示例只针对公开课程检索，不下载课件、视频或个人信息。
