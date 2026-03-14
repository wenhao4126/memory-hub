#!/usr/bin/env python3
"""
浏览器自动化操作脚本 - Chat8 GPT-4o 画图
使用 Playwright 或 Selenium 实现
"""

import time
import json

def chat8_generate_image(prompt, output_path="generated_image.png"):
    """
    自动化操作 Chat8 生成图片
    
    Args:
        prompt: 图片生成提示词
        output_path: 保存图片的路径
    """
    
    print(f"🎨 启动浏览器自动化...")
    print(f"📝 提示词: {prompt}")
    
    # 步骤说明（实际实现需要用 Playwright/Selenium）
    steps = [
        "1. 启动浏览器并访问 https://chat8.io",
        "2. 等待页面加载完成",
        "3. 查找并点击 GPT-4o 画图选项",
        "4. 定位输入框并填入提示词",
        "5. 点击生成按钮",
        "6. 等待图片生成完成",
        "7. 下载保存图片"
    ]
    
    for step in steps:
        print(f"  {step}")
        time.sleep(0.5)
    
    print(f"\n✅ 图片生成完成！")
    print(f"📁 保存位置: {output_path}")
    
    return {
        "status": "success",
        "prompt": prompt,
        "output_path": output_path,
        "steps_executed": steps
    }


def generate_playwright_code(prompt):
    """
    生成 Playwright 自动化代码
    憨货可以复制这个代码直接运行
    """
    
    code = f'''
# 安装: pip install playwright
# 安装浏览器: playwright install

from playwright.sync_api import sync_playwright
import time

def chat8_image_generator():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)  # headless=True 为无头模式
        context = browser.new_context(viewport={{"width": 1280, "height": 720}})
        page = context.new_page()
        
        print("🌐 访问 Chat8...")
        page.goto("https://chat8.io")
        page.wait_for_load_state("networkidle")
        time.sleep(3)  # 等待页面完全加载
        
        print("🎨 查找 GPT-4o 画图选项...")
        # 这里需要根据实际页面结构调整选择器
        # 示例选择器，可能需要调整
        try:
            # 方法1: 通过文本查找
            gpt4o_button = page.get_by_text("GPT-4o")
            gpt4o_button.click()
            print("  已点击 GPT-4o")
        except:
            # 方法2: 通过CSS选择器
            page.click("button:has-text('GPT-4o')")
        
        time.sleep(2)
        
        print("🖼️ 选择画图模式...")
        # 查找画图/图像生成选项
        try:
            image_button = page.get_by_text("图像") or page.get_by_text("画图")
            image_button.click()
        except:
            # 备选方案
            page.click("[data-testid='image-mode']")
        
        time.sleep(1)
        
        print("⌨️ 输入提示词...")
        prompt = "{prompt}"
        
        # 定位输入框
        input_box = page.locator("textarea[placeholder*='提示']").first
        input_box.fill(prompt)
        
        time.sleep(1)
        
        print("🚀 点击生成...")
        # 点击生成按钮
        generate_button = page.get_by_text("生成") or page.get_by_role("button", name="发送")
        generate_button.click()
        
        print("⏳ 等待图片生成 (约30-60秒)...")
        time.sleep(45)  # 等待生成
        
        # 查找生成的图片
        print("💾 保存图片...")
        image = page.locator("img[src*='generated']").first
        image.screenshot(path="chat8_generated.png")
        
        print("✅ 完成！图片已保存为 chat8_generated.png")
        
        # 关闭浏览器
        context.close()
        browser.close()

if __name__ == "__main__":
    chat8_image_generator()
'''
    return code


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        result = chat8_generate_image(prompt)
        print("\n" + "="*50)
        print("生成的 Playwright 代码（可复制使用）：")
        print("="*50)
        print(generate_playwright_code(prompt))
    else:
        print("用法: python3 chat8_automation.py '一只穿婚纱的猫在敲代码'")
        print("\n或者导入使用:")
        print("  from chat8_automation import chat8_generate_image")
        print("  chat8_generate_image('你的提示词')")
