#!/usr/bin/env python3
"""
小搜的 DuckDuckGo 搜索工具
完全免费，无需 API Key
"""

import urllib.request
import urllib.parse
import json
import re
from html.parser import HTMLParser

class DuckDuckGoSearch:
    """DuckDuckGo 搜索类"""
    
    def __init__(self):
        self.base_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search(self, query, max_results=5):
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            max_results: 最多返回结果数
            
        Returns:
            list: 搜索结果列表，每个结果是dict包含title, url, snippet
        """
        try:
            # 构建请求
            params = {'q': query}
            data = urllib.parse.urlencode(params).encode('utf-8')
            
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers=self.headers,
                method='POST'
            )
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # 解析结果
            results = self._parse_results(html, max_results)
            return results
            
        except Exception as e:
            print(f"搜索出错: {e}")
            return []
    
    def _parse_results(self, html, max_results):
        """解析 HTML 提取搜索结果"""
        results = []
        
        # 简单的正则提取（实际使用可能需要更完善的HTML解析）
        # 提取结果块
        result_pattern = r'<div class="result[^"]*"[^>]*>.*?<h2[^>]*class="result__title"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</h2>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>.*?</div>'
        
        matches = re.findall(result_pattern, html, re.DOTALL)
        
        for i, (url, title, snippet) in enumerate(matches[:max_results]):
            # 清理 HTML 标签
            title = self._clean_html(title)
            snippet = self._clean_html(snippet)
            
            results.append({
                'title': title,
                'url': url,
                'snippet': snippet
            })
        
        return results
    
    def _clean_html(self, text):
        """清理 HTML 标签"""
        # 移除所有 HTML 标签
        clean = re.sub(r'<[^>]+>', '', text)
        # 解码 HTML 实体
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&#39;', "'")
        return clean.strip()


# 便捷的搜索函数
def duck_search(query, max_results=5):
    """
    快速搜索函数
    
    用法:
        results = duck_search("Python教程", 3)
        for r in results:
            print(f"标题: {r['title']}")
            print(f"链接: {r['url']}")
            print(f"摘要: {r['snippet']}")
    """
    ddg = DuckDuckGoSearch()
    return ddg.search(query, max_results)


# 命令行测试
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"🔍 搜索: {query}\n")
        
        results = duck_search(query, 5)
        
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['title']}")
            print(f"   {r['url']}")
            print(f"   {r['snippet'][:100]}...\n")
    else:
        print("用法: python3 duckduckgo_search.py '搜索关键词'")
