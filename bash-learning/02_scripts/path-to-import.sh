#!/bin/bash

filepath="$1"
symbol="$2"  # 函数名 or 类名

if [ -z "$filepath" ] || [ -z "$symbol" ]; then
  echo "Usage: $0 path/to/file.py SymbolName"
  exit 1
fi

# 去掉 .py 后缀
module="${filepath%.py}"

# 替换 / 为 .
import_path=$(echo "$module" | tr '/' '.')

# 输出 Python import 语句
echo "from $import_path import $symbol"
