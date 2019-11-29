import re


class test:

  special_symbol = re.compile("[`~#^*+=|^&gt$|^&gte$|^&lt$|^&lte$|\u4e00-\u9fa5|{}\\[\\]<>/� \uE009\uF8F5amp;（）|【】‘；：”“’。，、？]")
  print (special_symbol)
  print("Hello, World!")
  pattern = r'><+-*/'  # 模式字符串
  str1 = '12312343+-'
  match = re.findall(pattern, str1)
  print(len(match))



