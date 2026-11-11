#!/bin/bash
# 双击本文件即可启动「微信 AI 回复助手」并打开浏览器
cd "$(dirname "$0")" || exit 1
( sleep 1; open "http://127.0.0.1:8787" ) &
exec python3 server.py
