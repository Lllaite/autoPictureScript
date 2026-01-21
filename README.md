# 通用网页自动化脚本

这是一个通用的网页自动化脚本，用于读取问题文件并在网站上自动提交问题并截图。

## 功能特性

- 📄 从文本文件读取问题列表
- 🌐 自动访问指定网站
- ⌨️ 在指定的文本区域输入问题
- 📤 自动提交问题（支持回车键或特定按钮）
- ⏱️ 等待AI回复完成
- 📸 自动截图保存
- 🔄 支持并行处理多个标签页
- 🎯 可配置的浏览器选项（Chrome/Firefox，有头/无头模式）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

1. **准备问题文件** (`questions.txt`)
   每行一个问题，例如：
   ```
   什么是人工智能？
   机器学习有哪些类型？
   深度学习与机器学习的区别是什么？
   ```

2. **配置脚本**
   ```bash
   # 复制示例配置文件
   cp config.example.json config.json
   
   # 编辑 config.json，填入你的网站信息
   ```
   
   编辑 `config.json`：
   ```json
   {
     "website_url": "https://your-chat-website.com",
     "textarea_selector": ".chat-input, textarea[placeholder*='输入']",
     "submit_selector": "button.send-button",
     "wait_time": 10,
     "browser": "chrome",
     "headless": false,
     "output_dir": "screenshots",
     "keep_browser_open": false
   }
   ```

3. **运行脚本**
   ```bash
   # 顺序处理
   python web_automation.py --questions questions.txt
   
   # 并行处理（最多3个标签页同时运行）
   python web_automation.py --questions questions.txt --parallel --workers 3
   
   # 指定输出目录
   python web_automation.py --questions questions.txt --output my_screenshots
   
   # 使用自定义配置文件
   python web_automation.py --questions questions.txt --config my_config.json
   ```

## 配置文件说明

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `website_url` | 目标网站URL | `"https://chat.example.com"` |
| `textarea_selector` | 文本区域的CSS选择器 | `"textarea.input-field"` |
| `submit_selector` | 提交按钮的CSS选择器（可选） | `"button[type='submit']"` |
| `wait_time` | 等待回复的时间（秒） | `10` |
| `browser` | 浏览器类型 | `"chrome"` 或 `"firefox"` |
| `headless` | 是否无头模式（不显示浏览器界面） | `false` |
| `output_dir` | 截图保存目录 | `"screenshots"` |
| `keep_browser_open` | 完成后是否保持浏览器打开 | `false` |

## CSS选择器查找方法

1. 打开目标网站
2. 右键点击文本输入框 → 检查
3. 在开发者工具中找到对应的HTML元素
4. 查看其class、id或其他属性
5. 编写CSS选择器，例如：
   - 按class: `.ant-input`
   - 按id: `#message-input`
   - 按属性: `[placeholder="输入消息"]`
   - 组合: `textarea.chat-input`

## 注意事项

1. **网站限制**：确保目标网站允许自动化操作，遵守网站的robots.txt和服务条款
2. **速率限制**：适当调整等待时间，避免对服务器造成过大压力
3. **反爬虫机制**：某些网站可能有反爬虫措施，需要相应处理
4. **浏览器驱动**：脚本会自动下载合适的浏览器驱动
5. **网络环境**：确保网络连接稳定

## 输出结果

- 截图保存在指定的输出目录中
- 文件名格式：`question_1_20250116_143022.png`
- 控制台会显示处理进度和结果摘要

## 故障排除

### 常见问题

1. **找不到元素**
   - 检查CSS选择器是否正确
   - 确认页面已完全加载
   - 尝试增加等待时间

2. **浏览器驱动问题**
   - 确保已安装对应浏览器
   - 检查网络连接是否能下载驱动

3. **截图不完整**
   - 对于长页面，脚本会自动滚动截图
   - 可以调整浏览器窗口大小

### 调试建议

1. 将 `headless` 设为 `false` 查看浏览器操作过程
2. 增加 `wait_time` 确保回复完全显示
3. 检查控制台输出的错误信息

## 高级用法

### 自定义等待条件
可以修改 `process_question` 方法中的等待逻辑，例如等待特定元素出现：
```python
# 等待回复消息出现
reply_element = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".reply-message"))
)
```

### 处理验证码
如果网站有验证码，需要手动干预或使用验证码识别服务

### 处理登录状态
如果需要登录，可以在配置中添加登录相关操作

## 许可证

通用开源许可证，请遵守相关法律法规和网站使用条款