#!/usr/bin/env python3
"""
AI 图片生成 - 免费API版
无需登录，直接生成
"""

import urllib.request
import urllib.parse
import json
import time

def generate_image_pollinations(prompt, width=1024, height=1024, seed=None):
    """
    使用 Pollinations.ai 免费生成图片
    无需API Key，无需登录，直接下载
    """
    
    print("🎨 正在生成图片...")
    print(f"📝 提示词: {prompt}")
    print()
    
    # Pollinations.ai 免费接口
    # 文档: https://pollinations.ai/
    
    # URL编码提示词
    encoded_prompt = urllib.parse.quote(prompt)
    
    # 构建URL
    seed_param = f"&seed={seed}" if seed else ""
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true{seed_param}"
    
    print(f"🌐 请求URL: {url[:80]}...")
    print()
    
    try:
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        print("⏳ 下载中...")
        with urllib.request.urlopen(req, timeout=120) as response:
            image_data = response.read()
            
            # 保存图片
            filename = f"generated_{int(time.time())}.png"
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            print(f"✅ 图片生成成功！")
            print(f"📁 保存为: {filename}")
            print(f"📏 尺寸: {width}x{height}")
            print(f"📊 大小: {len(image_data)/1024:.1f} KB")
            
            return filename
            
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return None


def main():
    """主函数"""
    import sys
    
    print("="*60)
    print("🎨 AI 图片生成器 (Pollinations.ai)")
    print("="*60)
    print()
    
    # 获取提示词
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("请输入图片生成提示词（中文/英文都可以）:\n")
    
    if not prompt:
        prompt = "一只穿着婚纱的猫坐在电脑前敲代码，表情既幸福又无奈，卡通插画风格，色彩明亮活泼"
        print(f"\n使用默认提示词: {prompt}")
    
    print()
    
    # 生成图片
    filename = generate_image_pollinations(prompt)
    
    if filename:
        print()
        print("="*60)
        print("✅ 完成！图片已保存到当前目录")
        print(f"📁 文件名: {filename}")
        print("="*60)
    else:
        print()
        print("❌ 生成失败，请检查网络连接")


if __name__ == "__main__":
    main()
