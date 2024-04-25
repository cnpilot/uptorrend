#!/bin/bash
#/home/boxbox/torcp/tuiso.sh  "%F"  "%N"  "%G"  "%D"  "%L"  "%R"  "%C"  "%Z"  "%I"
#对于有BDMV的目录，压缩iso并保存到BDMV的上一级目录然后删除文件夹，对于无BDMV文件夹的则直接退出脚本。
# mkdir -p /home/boxbox/logs
# chmod 777 /home/boxbox/logs

sleep 2
# qb4.3.9 path="$3"  qb4.5.4 path="$4"
path="$3"

cd "$path"

find . -type d -name "BDMV" | while read dir; do
    MV_PATH=$(dirname "$dir")
    MV_NAME=$(basename "$MV_PATH")
    ISO=".iso"
    LOG_FILE="/home/boxbox/logs/$MV_NAME.log"
    genisoimage -o "$(dirname "$MV_PATH")/$MV_NAME$ISO" -iso-level 4 -allow-lowercase -l -udf -allow-limited-size "$MV_PATH" > "$LOG_FILE" 2>&1 && rm -r "$MV_PATH"
done
