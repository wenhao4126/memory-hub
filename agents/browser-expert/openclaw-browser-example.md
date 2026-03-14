# OpenClaw Browser 操作示例 - Chat8 画图

## 前提条件
1. 安装 Chrome 浏览器
2. 安装 OpenClaw Chrome 扩展
3. 在目标网页上点击扩展图标连接

## 操作代码（傻妞执行）

```javascript
// 步骤1: 打开 Chat8
await browser({ 
  action: "open", 
  targetUrl: "https://chat8.io",
  target: "chrome"  // 使用 Chrome 扩展模式
});

// 步骤2: 获取页面快照，找到 GPT-4o 按钮
const snapshot = await browser({ action: "snapshot", refs: "aria" });
// 分析 snapshot 找到 GPT-4o 按钮的 ref

// 步骤3: 点击 GPT-4o 选项
await browser({
  action: "act",
  request: {
    kind: "click",
    ref: "gpt4o-button-ref"  // 从 snapshot 获取的实际 ref
  }
});

// 步骤4: 点击画图模式
await browser({
  action: "act",
  request: {
    kind: "click",
    ref: "image-mode-ref"
  }
});

// 步骤5: 输入提示词
await browser({
  action: "act",
  request: {
    kind: "type",
    ref: "input-box-ref",
    text: "一只穿婚纱的猫在敲代码，卡通风格"
  }
});

// 步骤6: 点击生成
await browser({
  action: "act",
  request: {
    kind: "click",
    ref: "generate-button-ref"
  }
});

// 步骤7: 等待并截图
await browser({ action: "screenshot", fullPage: true });
```

## 实际使用限制
- 需要人工在 Chrome 上连接扩展
- 元素 ref 会变化，需要动态获取
- 适合单次演示，不适合批量自动化
