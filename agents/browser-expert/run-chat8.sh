#!/bin/bash
# 一键启动浏览器专家，执行 Chat8 画图任务

PROMPT="${1:-一只穿婚纱的猫在敲代码，卡通风格，色彩明亮}"

echo "🎨 启动浏览器专家智能体..."
echo "📝 任务: 在 Chat8 用 GPT-4o 生成图片"
echo "💬 提示词: $PROMPT"
echo ""

# 使用 OpenClaw 创建智能体执行任务
openclaw sessions spawn \
  --runtime subagent \
  --mode run \
  --timeout 300 \
  --label browser-chat8 \
  --task "你是浏览器专家。请完成以下任务：

1. 使用 Playwright 或 browser 工具访问 https://chat8.io
2. 选择 GPT-4o 模型
3. 切换到画图模式
4. 输入提示词: $PROMPT
5. 生成图片并保存
6. 汇报结果

注意：
- 如果 browser 工具需要 Chrome 扩展，先用 Playwright
- 页面元素选择器可能需要调整
- 图片生成等待时间设置 60-120 秒
- 保存图片到工作目录

完成后汇报生成的图片位置。"

echo ""
echo "✅ 智能体已派出，正在执行任务..."
echo "📊 查看状态: openclaw subagents list"
