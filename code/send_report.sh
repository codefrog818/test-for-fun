#!/bin/bash

# 定位到脚本所在目录
cd /Users/yichenbao/Desktop/coding/test-for-fun/code

# 运行 Python 脚本，生成报告
python3 simple_info.py

# 输出当天的报告内容，快捷指令将以此为邮件正文
cat report_$(date +%F).txt
