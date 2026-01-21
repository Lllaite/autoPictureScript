#!/usr/bin/env python3
"""
通用网页自动化脚本
用于读取问题文件，在网站上自动提交问题并截图
"""

import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import os
from PIL import Image
from io import BytesIO
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebAutomation:
    def __init__(self, config):
        """
        初始化自动化工具
        
        Args:
            config (dict): 配置字典，包含以下键：
                - website_url: 网站URL
                - textarea_selector: 文本区域CSS选择器
                - submit_selector: 提交按钮CSS选择器（可选）
                - wait_time: 等待回复的时间（秒）
                - browser: 浏览器类型（chrome/firefox）
                - headless: 是否无头模式
                - output_dir: 输出目录
        """
        self.config = config
        self.drivers = []
        self.setup_output_dir()
        
    def setup_output_dir(self):
        """创建输出目录"""
        if not os.path.exists(self.config['output_dir']):
            os.makedirs(self.config['output_dir'])
            logger.info(f"创建输出目录: {self.config['output_dir']}")
            
    def create_driver(self):
        """创建浏览器驱动实例"""
        browser = self.config.get('browser', 'chrome').lower()
        headless = self.config.get('headless', False)
        
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            
        else:
            raise ValueError(f"不支持的浏览器: {browser}")
            
        return driver
    
    def process_question(self, question, index):
        """处理单个问题"""
        driver = None
        try:
            # 创建新的浏览器实例
            driver = self.create_driver()
            self.drivers.append(driver)
            
            logger.info(f"处理问题 {index}: {question[:50]}...")
            
            # 访问网站
            driver.get(self.config['website_url'])
            
            # 等待页面加载
            wait = WebDriverWait(driver, 10)
            
            # 找到文本区域
            textarea = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.config['textarea_selector']))
            )
            
            # 输入问题
            textarea.clear()
            textarea.send_keys(question)
            
            # 提交问题
            submit_selector = self.config.get('submit_selector')
            if submit_selector:
                # 如果有特定的提交按钮选择器
                submit_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector))
                )
                submit_button.click()
            else:
                # 否则尝试按回车键
                textarea.send_keys(Keys.RETURN)
            
            # 等待回复完成
            logger.info(f"等待回复完成，等待 {self.config['wait_time']} 秒...")
            time.sleep(self.config['wait_time'])
            
            # 截图
            screenshot_path = os.path.join(
                self.config['output_dir'], 
                f"question_{index}_{time.strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            # 获取完整页面截图
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            if total_height > viewport_height:
                # 长页面，需要滚动截图
                driver.set_window_size(1920, total_height)
                time.sleep(1)
            
            driver.save_screenshot(screenshot_path)
            logger.info(f"截图保存到: {screenshot_path}")
            
            return index, True, screenshot_path
            
        except Exception as e:
            logger.error(f"处理问题 {index} 时出错: {str(e)}")
            return index, False, str(e)
            
        finally:
            # 保持浏览器打开，或者可以选择关闭
            if driver and self.config.get('keep_browser_open', False):
                pass  # 保持浏览器打开
            # 否则会在所有任务完成后统一关闭
    
    def process_questions_parallel(self, questions, max_workers=3):
        """并行处理多个问题"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(self.process_question, question, i): (i, question)
                for i, question in enumerate(questions, 1)
            }
            
            # 收集结果
            for future in as_completed(futures):
                i, question = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"任务 {i} 执行失败: {str(e)}")
                    results.append((i, False, str(e)))
        
        return results
    
    def process_questions_sequential(self, questions):
        """顺序处理多个问题"""
        results = []
        
        for i, question in enumerate(questions, 1):
            result = self.process_question(question, i)
            results.append(result)
            
            # 每个问题处理完成后等待一下
            time.sleep(2)
        
        return results
    
    def close_all_drivers(self):
        """关闭所有浏览器驱动"""
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        self.drivers = []
        logger.info("所有浏览器驱动已关闭")
    
    def run(self, questions_file, parallel=True, max_workers=3):
        """运行自动化任务"""
        # 读取问题文件
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
            
            if not questions:
                logger.error("问题文件为空")
                return []
                
            logger.info(f"读取到 {len(questions)} 个问题")
            
        except Exception as e:
            logger.error(f"读取问题文件失败: {str(e)}")
            return []
        
        # 处理问题
        try:
            if parallel:
                results = self.process_questions_parallel(questions, max_workers)
            else:
                results = self.process_questions_sequential(questions)
            
            # 打印统计信息
            success_count = sum(1 for r in results if r[1])
            logger.info(f"处理完成: {success_count}/{len(questions)} 成功")
            
            return results
            
        finally:
            # 关闭所有浏览器驱动
            if not self.config.get('keep_browser_open', False):
                self.close_all_drivers()

def main():
    parser = argparse.ArgumentParser(description='通用网页自动化脚本')
    parser.add_argument('--questions', '-q', required=True, help='问题文件路径')
    parser.add_argument('--config', '-c', default='config.json', help='配置文件路径（JSON格式）')
    parser.add_argument('--parallel', '-p', action='store_true', help='启用并行处理')
    parser.add_argument('--workers', '-w', type=int, default=3, help='并行工作线程数')
    parser.add_argument('--output', '-o', default='screenshots', help='输出目录')
    
    args = parser.parse_args()
    
    # 默认配置（用户应该创建自己的配置文件）
    default_config = {
        'website_url': 'YOUR_WEBSITE_URL_HERE',  # 需要用户填写
        'textarea_selector': 'YOUR_TEXTAREA_CSS_SELECTOR',  # 需要用户填写
        'submit_selector': '',  # 可选，如果需要特定提交按钮
        'wait_time': 10,  # 等待回复的时间（秒）
        'browser': 'chrome',  # chrome 或 firefox
        'headless': False,  # 是否无头模式
        'output_dir': args.output,
        'keep_browser_open': False  # 处理完成后是否保持浏览器打开
    }
    
    # 检查配置文件是否存在
    config_file = args.config
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            # 用用户配置更新默认配置
            default_config.update(user_config)
            logger.info(f"使用配置文件: {config_file}")
        except Exception as e:
            logger.warning(f"读取配置文件失败，使用默认配置: {str(e)}")
    else:
        # 创建示例配置文件
        try:
            import json
            with open('config.example.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info("已创建示例配置文件: config.example.json")
            logger.info("请编辑此文件并填入正确的网站URL和CSS选择器")
            return
        except:
            pass
    
    # 检查配置是否已更新
    if default_config['website_url'] == 'YOUR_WEBSITE_URL_HERE':
        logger.error("请先配置网站URL和CSS选择器")
        logger.error("1. 编辑 config.example.json 文件")
        logger.error("2. 填入正确的网站URL和CSS选择器")
        logger.error("3. 重命名为 config.json 或使用 --config 参数指定")
        return
    
    # 运行自动化
    automation = WebAutomation(default_config)
    results = automation.run(args.questions, args.parallel, args.workers)
    
    # 输出结果摘要
    print("\n" + "="*50)
    print("处理结果摘要:")
    print("="*50)
    for idx, success, info in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"问题 {idx}: {status}")
        if success:
            print(f"  截图: {info}")
        else:
            print(f"  错误: {info}")
    print("="*50)

if __name__ == '__main__':
    main()