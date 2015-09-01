#!/bin/bash

if [ ! -d "$1" ]; then
  echo "Please run $0 <directory>"
  echo "You'll find errors in errors.log and the output will be logged in run.log"
  exit 1
fi

python photofix.py "$1" 2>errors.log | tee run.log

