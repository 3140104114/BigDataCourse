# 定义：告诉 Python 这项任务怎么做
def clean_title(text):
  title = text.strip()
  print(f"原始标题：{text} → 清理后标题：{title}")
  
  # return title

# 调用：真正执行里面的代码
result = clean_title(" 招聘公告 ")
print(result) # 招聘公告