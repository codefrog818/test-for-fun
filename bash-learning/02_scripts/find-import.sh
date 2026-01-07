#!/bin/bash

target="$1"

if [ -z "$target" ]; then
  echo "Usage: $0 <class_or_function_name>"
  exit 1
fi

# 自动找到 project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 搜索 code 目录内的 .py 文件，查 class 或 def 定义（支持括号或冒号结尾）
result=$(grep -rEl "^(class|def)[[:space:]]+$target[[:space:]]*[\(:]" "$PROJECT_ROOT/code" --include="*.py")

if [ -z "$result" ]; then
  echo "'$target' not found in $PROJECT_ROOT/code."
  exit 1
fi

# 取第一个匹配
first_file=$(echo "$result" | head -n 1)

# 生成 import 路径
relpath="${first_file#$PROJECT_ROOT/}"
modpath="${relpath%.py}"
import_path=$(echo "$modpath" | tr '/' '.')

echo "from $import_path import $target"
