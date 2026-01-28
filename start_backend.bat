@echo off
chcp 65001 >nul
echo ====================================
echo 启动后端 API 服务
echo ====================================
echo.
echo 正在启动后端服务...
echo （后端会自动选择可用端口）
echo.
cd backend
python api.py
cd ..
