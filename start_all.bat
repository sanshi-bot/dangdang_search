@echo off
chcp 65001 >nul
echo ====================================
echo 当当网图书爬虫 Web 应用
echo ====================================
echo.
echo 正在启动后端服务...
echo （后端会自动选择可用端口 8000-8009）
cd backend
start "后端API服务" cmd /k "python api.py"
cd ..
echo.
echo 等待后端服务启动...
timeout /t 8 /nobreak >nul
echo.
echo 正在打开前端页面...
echo （前端会自动检测后端端口）
start "" "frontend/home.html"
echo.
echo ====================================
echo 启动完成！
echo ====================================
echo 后端会自动选择可用端口（8000-8009）
echo 前端会自动检测后端端口
echo 请查看后端窗口了解实际使用的端口
echo ====================================
echo.
