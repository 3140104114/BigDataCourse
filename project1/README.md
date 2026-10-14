# 项目一：招录招聘公告采集（参考答案）

本目录是完整参考答案；未完成的学生框架位于 [student](student/) 目录。两者使用相同的函数结构，便于逐项讲解和对照。

采集对象为襄阳市人力资源和社会保障局“招录招聘”栏目前 30 页公开公告。栏目入口：<http://rsj.xiangyang.gov.cn/xwzx/zlzp/>。

## 程序结构

[crawler.py](crawler.py) 包含以下主要函数：

- `build_url()`：根据逻辑页码构造列表页 URL。
- `fetch_page()`：请求页面、检查 HTTP 状态并保存原始 HTML。
- `parse_page()`：使用 XPath 提取公告的六个字段。
- `save_csv()`：以 UTF-8 with BOM 编码保存 CSV。
- `save_summary()`：保存简要运行结果。
- `main()`：循环采集、处理异常、汇总并保存结果。

参考答案与学生框架的分工如下：

| 内容 | 学生是否完成 |
| --- | --- |
| `build_url()` | 是 |
| `fetch_page()` | 是 |
| `parse_page()` | 是 |
| `save_csv()` | 是 |
| `main()` 中的函数调用 | 是 |
| 配置、异常处理、摘要 | 教师提供 |

## 字段说明

| 字段 | 处理规则 |
| --- | --- |
| `title` | 读取链接的完整 `title` 属性并去除首尾空白 |
| `publish_date` | 使用列表页日期，统一为 `YYYY-MM-DD`；缺失时留空并提示 |
| `detail_url` | 使用页面真实 `href`，通过 `urljoin()` 转为绝对 URL |
| `source_url` | 当前公告所在列表页 URL |
| `page` | 从 1 开始的逻辑页码 |
| `collected_at` | 带 `UTC+08:00` 时区的采集时间 |

网页一页包含多个 `ul.news-list`，参考答案一次选择其中全部公告 `li`。标题使用 `title` 属性，避免保存页面上被省略号截断的显示文本。

## 安装与运行

```powershell
cd E:\code\BigDataCourse\project1
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe crawler.py
```

参考答案默认 `MAX_PAGES = 30`。课堂演示或测试时，先临时改为 `1`，核对首页字段和条数后再恢复为 `30`。

程序使用固定的输出目录，重新运行时会更新原有结果：

```text
data/raw/page_N.html             成功请求的原始列表页
data/output/announcements.csv    按列表顺序汇总的公告数据
logs/failed_pages.csv            失败页及原因；无失败时只有表头
logs/run_summary.txt             页数、条数和完成状态
```

发生请求失败、HTTP 错误或页面结构异常时，程序记录当前页并停止。失败不能当作网站末页，也不进行自动重试或访问限制绕过。

## 结果核对

正式提交前仍需人工检查：

- 首页、第二页和第 30 页 URL 是否符合真实分页规则。
- 网页实际公告条数与程序解析条数是否一致。
- CSV 六列顺序、日期格式和中文编码是否正确。
- 标题及详情链接是否为空。
- 抽查首页、中间页和第 30 页的记录是否与原网页一致。

参考答案保持与第 5 次课相近的难度，不包含单元测试框架、JSON 摘要或复杂日志系统。
