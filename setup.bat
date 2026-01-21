@echo off
echo 正在安装Python依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo 安装失败，请检查Python和pip是否正确安装
    pause
    exit /b 1
)

echo.
echo 安装完成！
echo.
echo 请按以下步骤配置：
echo 1. 复制 config.example.json 为 config.json
echo 2. 编辑 config.json，填入正确的网站URL和CSS选择器
echo 3. 准备 questions.txt 文件，每行一个问题
echo 4. 运行脚本：python web_automation.py --questions questions.txt
echo.
pause