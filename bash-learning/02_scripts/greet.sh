#!/bin/bash

name=$1
if [ -z "$name" ]; then
  echo "Usage: ./greet.sh <your-name>"
  exit 1
fi

echo "Hello, $name!"
