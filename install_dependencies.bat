@echo off
chcp 65001 >nul
echo ====================================
echo 安装项目依赖
echo ====================================
echo.
echo 正在使用清华镜像源安装 Python 依赖包...
echo 镜像源: https://pypi.tuna.tsinghua.edu.cn/simple
echo.

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

echo.
echo ====================================
echo 安装完成！
echo ====================================
echo.
echo 运行环境检查脚本...
echo.
python check_environment.py
echo.
pause
