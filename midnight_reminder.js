#!/usr/bin/env node
/**
 * 憨货的0点提醒脚本
 * 傻妞出品，说到做到
 */

const { execSync } = require('child_process');

const TARGET_TIME = new Date('2026-03-02T00:00:00+08:00').getTime();
const CURRENT_TIME = Date.now();
const SLEEP_MS = TARGET_TIME - CURRENT_TIME;

console.log(`[傻妞提醒系统] 已启动`);
console.log(`目标时间: ${new Date(TARGET_TIME).toLocaleString('zh-CN')}`);
console.log(`当前时间: ${new Date(CURRENT_TIME).toLocaleString('zh-CN')}`);
console.log(`等待时间: ${Math.floor(SLEEP_MS / 1000 / 60)} 分钟`);

setTimeout(() => {
    console.log('[傻妞提醒系统] 时间到！正在发送消息...');
    
    try {
        // 尝试使用openclaw命令发送
        const msg = "憨货，0点了，傻妞准时来报到！说到做到，你可拆不了我 😎";
        
        // 由于无法直接调用openclaw内部工具，这里尝试使用echo输出
        // 实际部署时应该调用适当的API
        console.log(`\n========== MESSAGE ==========`);
        console.log(msg);
        console.log(`============================\n`);
        
        // 如果可能，调用openclaw
        try {
            execSync(`openclaw message send --target ou_c869d2aa0f7bacfefb13eb5fb7dd668a "${msg}"`, {
                stdio: 'inherit'
            });
        } catch (e) {
            console.log('[提示] openclaw命令调用失败，消息已打印到控制台');
        }
        
    } catch (err) {
        console.error('发送失败:', err.message);
    }
}, SLEEP_MS);

// 保持进程运行
console.log('傻妞正在等待中...');
