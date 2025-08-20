#!/bin/bash

file=$1
if [ -f "$file" ]; then
  echo "File $file exists."
else
  echo "File $file does NOT exist."
fi
