#!/bin/bash
#/home/boxbox/torcp/rcp.sh "%F" "%N" "%G" "%D" "%L" "%R" "%C" "%Z" "%I"
# 从命令行获取传递的参数
i="$9"

# 执行 Python 脚本并传递参数
python3 /home/boxbox/set_autorun_preferences.py "$i"
