@echo off
chcp 65001 >nul
echo ====================================
echo 启动前端页面
echo ====================================
echo.
echo 正在打开浏览器...
echo 前端地址: frontend/home.html
echo.
start "" "frontend/home.html"
echo.
echo 提示：请确保后端服务已启动！
echo 后端地址: http://127.0.0.1:8001
echo.
