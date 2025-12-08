#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博客文章生成工具 - 动态模式版
使用JavaScript动态解析Markdown文件
"""

import os
import re
import shutil
import json
from datetime import datetime
from html import escape, unescape
import sys

def get_all_post_files():
    """获取所有文章文件列表"""
    # 查找HTML文件
    html_files = [f for f in os.listdir('.') if f.startswith('post') and f.endswith('.html')]
    
    # 按编号排序
    def extract_number(filename):
        match = re.search(r'post(\d+)\.html', filename)
        return int(match.group(1)) if match else 0
    
    html_files.sort(key=extract_number)
    return html_files

def get_next_post_number():
    """获取下一个文章编号"""
    post_files = get_all_post_files()
    if not post_files:
        return 1
    
    numbers = []
    for f in post_files:
        match = re.search(r'post(\d+)\.html', f)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers) + 1 if numbers else 1

def calculate_reading_time(content):
    """根据内容估算阅读时间"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'[a-zA-Z]+', content))
    minutes = (chinese_chars / 300) + (english_words / 200)
    return max(1, int(minutes))

def parse_markdown_file(md_file_path):
    """解析 Markdown 文件，提取元数据和内容"""
    if not os.path.exists(md_file_path):
        print(f"错误: 找不到文件 {md_file_path}")
        return None
    
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    post_data = {}
    
    # 检查是否有 YAML front matter
    front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if front_matter_match:
        # 有 front matter，解析元数据
        front_matter = front_matter_match.group(1)
        post_data['content'] = front_matter_match.group(2).strip()
        
        # 解析 front matter 中的键值对
        for line in front_matter.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if key == 'title':
                    post_data['title'] = value
                elif key == 'category':
                    post_data['category'] = value
                elif key == 'date':
                    post_data['date'] = value
                elif key == 'cover_image':
                    post_data['cover_image'] = value
                elif key == 'excerpt':
                    post_data['excerpt'] = value
                elif key == 'tags':
                    post_data['tags'] = [tag.strip() for tag in value.split(',') if tag.strip()]
    else:
        # 没有 front matter，使用文件名和默认值
        post_data['content'] = content.strip()
        
        # 从文件名提取标题（去掉扩展名）
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        post_data['title'] = base_name
    
    # 设置默认值
    if 'title' not in post_data or not post_data['title']:
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        post_data['title'] = base_name
    
    if 'category' not in post_data:
        post_data['category'] = '其他'
    
    if 'date' not in post_data:
        post_data['date'] = datetime.now().strftime("%Y年%m月%d日")
    
    if 'cover_image' not in post_data:
        post_data['cover_image'] = "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80"
    
    if 'excerpt' not in post_data:
        # 从内容前几行提取摘要
        content_lines = post_data['content'].split('\n')
        excerpt = ''
        for line in content_lines[:3]:
            line = line.strip()
            if line and not line.startswith('#'):
                excerpt = line[:100]  # 取前100个字符
                break
        post_data['excerpt'] = excerpt if excerpt else "点击阅读全文..."
    
    if 'tags' not in post_data:
        post_data['tags'] = []
    
    # 计算阅读时间
    post_data['reading_time'] = calculate_reading_time(post_data['content'])
    
    # 动态模式标记
    post_data['mode'] = 'dynamic'
    
    return post_data

def create_post_html(post_data, post_filename):
    """生成动态解析Markdown的文章页面 HTML"""
    # 获取对应的Markdown文件名
    md_filename = post_filename.replace('.html', '.md')
    
    post_template = '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | 博客世界</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Marked.js 库 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- Prism.js 代码高亮 -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markdown.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-csharp.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet">
    <style>
        /* 全局样式 */
        :root {{
            --primary-color: #4a6fa5;
            --secondary-color: #32a852;
            --text-color: #333;
            --text-light: #6c757d;
            --background-color: #f5f7fa;
            --card-bg: #ffffff;
            --border-color: #eaeaea;
            --shadow: 0 4px 12px rgba(0,0,0,0.05);
            --shadow-heavy: 0 8px 24px rgba(0,0,0,0.1);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.8;
            font-size: 16px;
        }}
        
        a {{
            color: var(--primary-color);
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        a:hover {{
            color: var(--secondary-color);
            text-decoration: underline;
        }}
        
        /* 布局容器 */
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        /* 头部样式 */
        header {{
            background-color: var(--card-bg);
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            background-color: rgba(255, 255, 255, 0.95);
        }}
        
        .header-inner {{
            max-width: 900px;
            margin: 0 auto;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--primary-color);
        }}
        
        .logo span {{
            color: var(--secondary-color);
        }}
        
        .back-link {{
            color: var(--primary-color);
            text-decoration: none;
            font-size: 0.95rem;
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 4px;
            background-color: rgba(74, 111, 165, 0.1);
        }}
        
        .back-link i {{
            margin-right: 6px;
        }}
        
        .back-link:hover {{
            background-color: rgba(74, 111, 165, 0.2);
            text-decoration: none;
        }}
        
        /* 文章头部 */
        .article-header {{
            margin-top: 40px;
            margin-bottom: 30px;
            padding: 20px;
            background-color: var(--card-bg);
            border-radius: 12px;
            box-shadow: var(--shadow);
        }}
        
        .article-title {{
            font-size: 2.2rem;
            margin-bottom: 15px;
            color: #166088;
            line-height: 1.3;
        }}
        
        .article-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            align-items: center;
            color: var(--text-light);
            font-size: 0.9rem;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }}
        
        .article-meta-item {{
            display: flex;
            align-items: center;
        }}
        
        .article-meta-item i {{
            margin-right: 6px;
            font-size: 0.9em;
        }}
        
        .mode-badge {{
            background-color: rgba(50, 168, 82, 0.1);
            color: var(--secondary-color);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        /* 封面图片 */
        .article-cover {{
            margin: 30px 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-heavy);
        }}
        
        .article-cover img {{
            width: 100%;
            height: 320px;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}
        
        .article-cover:hover img {{
            transform: scale(1.02);
        }}
        
        /* Markdown 内容区域 */
        .markdown-content {{
            font-size: 1.05rem;
            line-height: 1.7;
            margin: 40px 0;
        }}
        
        .markdown-content > *:first-child {{
            margin-top: 0 !important;
        }}
        
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3,
        .markdown-content h4 {{
            margin-top: 2em;
            margin-bottom: 1em;
            color: #166088;
            font-weight: 600;
            line-height: 1.3;
        }}
        
        .markdown-content h1 {{
            font-size: 1.8rem;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
        }}
        
        .markdown-content h2 {{
            font-size: 1.5rem;
        }}
        
        .markdown-content h3 {{
            font-size: 1.2rem;
        }}
        
        .markdown-content h4 {{
            font-size: 1.1rem;
        }}
        
        .markdown-content p {{
            margin: 1.2em 0;
            text-align: justify;
        }}
        
        .markdown-content img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 2em auto;
            border-radius: 8px;
            box-shadow: var(--shadow);
        }}
        
        .markdown-content ul,
        .markdown-content ol {{
            margin: 1.2em 0 1.2em 2em;
        }}
        
        .markdown-content li {{
            margin-bottom: 0.5em;
        }}
        
        .markdown-content li > ul,
        .markdown-content li > ol {{
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }}
        
        .markdown-content blockquote {{
            border-left: 4px solid var(--primary-color);
            padding: 1em 1.5em;
            margin: 2em 0;
            background-color: rgba(74, 111, 165, 0.05);
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: #555;
        }}
        
        .markdown-content blockquote p:last-child {{
            margin-bottom: 0;
        }}
        
        .markdown-content hr {{
            margin: 2.5em 0;
            border: none;
            border-top: 1px solid var(--border-color);
        }}
        
        .markdown-content table {{
            width: 100%;
            margin: 1.5em 0;
            border-collapse: collapse;
            font-size: 0.95em;
        }}
        
        .markdown-content th,
        .markdown-content td {{
            padding: 0.75em 1em;
            border: 1px solid var(--border-color);
            text-align: left;
        }}
        
        .markdown-content th {{
            background-color: rgba(74, 111, 165, 0.1);
            font-weight: 600;
        }}
        
        .markdown-content tr:nth-child(even) {{
            background-color: rgba(0, 0, 0, 0.02);
        }}
        
        .markdown-content code:not(pre code) {{
            background-color: rgba(0, 0, 0, 0.08);
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9em;
            color: #d63384;
        }}
        
        /* 代码块样式 */
        .code-block-wrapper {{
            margin: 2em 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: var(--shadow-heavy);
        }}
        
        .code-block-header {{
            background-color: #1a1a1a;
            color: #e2e8f0;
            padding: 0.75em 1.25em;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.85rem;
        }}
        
        .code-language {{
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .copy-button {{
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0.4em 1em;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}
        
        .copy-button:hover {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
        
        .copy-button.copied {{
            background-color: #38a169;
            border-color: #38a169;
        }}
        
        pre[class*="language-"] {{
            margin: 0 !important;
            border-radius: 0 !important;
            font-family: 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
            font-size: 0.95em !important;
        }}
        
        pre.line-numbers {{
            position: relative;
            padding-left: 3.8em;
            counter-reset: linenumber;
        }}
        
        .line-numbers .line-numbers-rows {{
            position: absolute;
            pointer-events: none;
            top: 0;
            font-size: 100%;
            left: -3.8em;
            width: 3em;
            letter-spacing: -1px;
            border-right: 1px solid #999;
            user-select: none;
        }}
        
        .line-numbers-rows > span {{
            display: block;
            counter-increment: linenumber;
        }}
        
        .line-numbers-rows > span:before {{
            content: counter(linenumber);
            color: #999;
            display: block;
            padding-right: 0.8em;
            text-align: right;
        }}
        
        /* 标签列表 */
        .tag-list {{
            margin-top: 40px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .tag-list span {{
            background-color: rgba(74, 111, 165, 0.1);
            color: var(--primary-color);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .tag-list span:hover {{
            background-color: rgba(74, 111, 165, 0.2);
            transform: translateY(-1px);
        }}
        
        /* 加载指示器 */
        .loading-indicator {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-light);
            background-color: var(--card-bg);
            border-radius: 12px;
            margin: 40px 0;
            box-shadow: var(--shadow);
        }}
        
        .loading-indicator i {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            color: var(--primary-color);
        }}
        
        .loading-indicator p {{
            font-size: 1rem;
            margin-top: 10px;
        }}
        
        /* 错误提示 */
        .error-container {{
            text-align: center;
            padding: 60px 20px;
            background-color: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 12px;
            margin: 40px 0;
            color: #c53030;
        }}
        
        .error-container i {{
            font-size: 2.5rem;
            margin-bottom: 15px;
        }}
        
        /* 页脚 */
        footer {{
            text-align: center;
            padding: 40px 20px;
            font-size: 0.9rem;
            color: var(--text-light);
            margin-top: 60px;
            border-top: 1px solid var(--border-color);
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 0 15px;
            }}
            
            .header-inner {{
                padding: 12px 15px;
            }}
            
            .article-title {{
                font-size: 1.8rem;
            }}
            
            .markdown-content h1 {{
                font-size: 1.5rem;
            }}
            
            .markdown-content h2 {{
                font-size: 1.3rem;
            }}
            
            .markdown-content h3 {{
                font-size: 1.1rem;
            }}
            
            .article-cover img {{
                height: 220px;
            }}
            
            .article-meta {{
                gap: 10px;
            }}
            
            .article-meta-item {{
                font-size: 0.85rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .article-title {{
                font-size: 1.5rem;
            }}
            
            .article-cover img {{
                height: 180px;
            }}
            
            .article-meta {{
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }}
            
            .code-block-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
                padding: 0.75em;
            }}
            
            .copy-button {{
                align-self: stretch;
                justify-content: center;
            }}
        }}
        
        /* 动画效果 */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .markdown-content > * {{
            animation: fadeIn 0.3s ease-out forwards;
        }}
        
        /* 深色模式支持 */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --primary-color: #63b3ed;
                --secondary-color: #68d391;
                --text-color: #e2e8f0;
                --text-light: #a0aec0;
                --background-color: #1a202c;
                --card-bg: #2d3748;
                --border-color: #4a5568;
                --shadow: 0 4px 12px rgba(0,0,0,0.3);
                --shadow-heavy: 0 8px 24px rgba(0,0,0,0.4);
            }}
            
            body {{
                background-color: var(--background-color);
                color: var(--text-color);
            }}
            
            .markdown-content code:not(pre code) {{
                background-color: rgba(255, 255, 255, 0.1);
                color: #fbb6ce;
            }}
            
            .markdown-content blockquote {{
                background-color: rgba(99, 179, 237, 0.1);
            }}
            
            .tag-list span {{
                background-color: rgba(99, 179, 237, 0.2);
                color: var(--primary-color);
            }}
            
            .loading-indicator {{
                background-color: var(--card-bg);
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <div class="logo"><span>博客</span>世界</div>
            <a href="index.html#blog" class="back-link"><i class="fas fa-arrow-left"></i>返回博客列表</a>
        </div>
    </header>

    <main class="container">
        <article>
            <header class="article-header">
                <h1 class="article-title">{title}</h1>
                <div class="article-meta">
                    <div class="article-meta-item">
                        <i class="fas fa-folder"></i>
                        <span>{category}</span>
                    </div>
                    <div class="article-meta-item">
                        <i class="fas fa-calendar-alt"></i>
                        <span>{date}</span>
                    </div>
                    <div class="article-meta-item">
                        <i class="fas fa-clock"></i>
                        <span>阅读时间：{reading_time} 分钟</span>
                    </div>
                    <div class="article-meta-item">
                        <span class="mode-badge">
                            <i class="fas fa-sync-alt"></i> 动态解析模式
                        </span>
                    </div>
                </div>
            </header>

            <div class="article-cover">
                <img src="{cover_image}" alt="{title}" loading="lazy">
            </div>
            
            <div class="loading-indicator" id="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>正在加载文章内容...</p>
                <p class="loading-hint">文章从 Markdown 文件动态解析，确保网络连接正常</p>
            </div>
            
            <div class="error-container" id="error-container" style="display: none;">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>内容加载失败</h3>
                <p id="error-message">未知错误</p>
                <button onclick="loadAndRenderMarkdown()" class="copy-button" style="margin-top: 15px;">
                    <i class="fas fa-redo"></i> 重试加载
                </button>
            </div>
            
            <div class="markdown-content" id="markdown-content" style="display: none;">
                <!-- Markdown内容将通过JavaScript动态渲染到这里 -->
            </div>
            
            <div class="tag-list">
{tags}
            </div>
        </article>
    </main>

    <footer>
        <p>© {current_year} 博客世界. 保留所有权利.</p>
        <p style="margin-top: 10px; font-size: 0.85rem; color: #888;">
            文章采用动态解析技术，内容实时从 Markdown 文件加载
        </p>
    </footer>
    
    <script>
    // 等待所有外部库加载完成
    let librariesLoaded = false;
    let markdownLoaded = false;
    let prismLoaded = false;
    
    // 检查marked库是否已加载
    function checkMarkedLoaded() {{
        if (typeof marked !== 'undefined') {{
            console.log('marked.js 已加载');
            markdownLoaded = true;
            checkAllLibrariesLoaded();
        }} else {{
            console.warn('marked.js 未加载，正在重试...');
            setTimeout(checkMarkedLoaded, 500);
        }}
    }}
    
    // 检查Prism库是否已加载
    function checkPrismLoaded() {{
        if (typeof Prism !== 'undefined') {{
            console.log('Prism.js 已加载');
            prismLoaded = true;
            checkAllLibrariesLoaded();
        }} else {{
            console.warn('Prism.js 未加载，正在重试...');
            setTimeout(checkPrismLoaded, 500);
        }}
    }}
    
    // 检查所有库是否已加载
    function checkAllLibrariesLoaded() {{
        if (markdownLoaded && prismLoaded && !librariesLoaded) {{
            librariesLoaded = true;
            console.log('所有库已加载完成，开始初始化');
            initializeMarked();
            // 延迟加载Markdown内容，确保DOM完全加载
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', startLoadingMarkdown);
            }} else {{
                startLoadingMarkdown();
            }}
        }}
    }}
    
    // 初始化marked.js
    function initializeMarked() {{
        if (typeof marked !== 'undefined') {{
            // 配置marked.js
            marked.setOptions({{
                breaks: true,           // 支持换行符
                gfm: true,             // 支持GitHub风格的Markdown
                headerIds: true,       // 自动生成标题ID
                smartypants: true,     // 智能引号和破折号
                highlight: function(code, lang) {{
                    if (lang && typeof Prism !== 'undefined' && Prism.languages[lang]) {{
                        try {{
                            return Prism.highlight(code, Prism.languages[lang], lang);
                        }} catch (e) {{
                            console.warn('Prism高亮失败:', e);
                            return code;
                        }}
                    }}
                    return code;
                }},
                langPrefix: 'language-',
            }});
            console.log('marked.js 初始化完成');
        }} else {{
            console.error('marked.js 未定义，无法初始化');
        }}
    }}
    
    // 开始加载Markdown
    function startLoadingMarkdown() {{
        console.log('开始加载Markdown内容');
        setTimeout(loadAndRenderMarkdown, 100);
    }}
    
    // 加载和渲染Markdown文件
    async function loadAndRenderMarkdown() {{
        try {{
            // 首先检查库是否已加载
            if (!librariesLoaded) {{
                throw new Error('必要的JavaScript库尚未加载完成，请稍后再试');
            }}
            
            if (typeof marked === 'undefined') {{
                throw new Error('marked.js 库加载失败');
            }}
            
            // 隐藏错误提示，显示加载指示器
            document.getElementById('error-container').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('markdown-content').style.display = 'none';
            
            // 获取Markdown文件名
            const mdFile = '{md_filename}';
            
            // 加载Markdown文件
            const response = await fetch(mdFile, {{
                cache: 'no-store'
            }});
            
            if (!response.ok) {{
                if (response.status === 404) {{
                    throw new Error('找不到Markdown文件: ' + mdFile);
                }} else {{
                    throw new Error('HTTP错误! 状态码: ' + response.status);
                }}
            }}
            
            const markdownText = await response.text();
            
            if (!markdownText.trim()) {{
                throw new Error('Markdown文件为空');
            }}
            
            // 解析YAML front matter
            let content = markdownText;
            
            // 检查是否有front matter
            const frontMatterRegex = /^---\\s*\\n([\\s\\S]*?)\\n---\\s*\\n([\\s\\S]*)$/;
            const match = markdownText.match(frontMatterRegex);
            
            if (match) {{
                content = match[2];
            }}
            
            // 将Markdown转换为HTML
            let html = marked.parse(content);
            
            // 处理代码块，添加复制按钮
            html = html.replace(
                /<pre><code class="language-(.*?)">([\\s\\S]*?)<\\/code><\\/pre>/g,
                function(match, lang, code) {{
                    return `
<div class="code-block-wrapper">
  <div class="code-block-header">
    <span class="code-language">${{lang}}</span>
    <button class="copy-button" onclick="copyCode(this)">
      <i class="fas fa-copy"></i> 复制代码
    </button>
  </div>
  <pre class="line-numbers language-${{lang}}"><code class="language-${{lang}}">${{code}}</code></pre>
</div>`;
                }}
            );
            
            // 处理没有语言标签的代码块
            html = html.replace(
                /<pre><code>([\\s\\S]*?)<\\/code><\\/pre>/g,
                function(match, code) {{
                    return `
<div class="code-block-wrapper">
  <div class="code-block-header">
    <span class="code-language">Text</span>
    <button class="copy-button" onclick="copyCode(this)">
      <i class="fas fa-copy"></i> 复制代码
    </button>
  </div>
  <pre class="line-numbers"><code>${{code}}</code></pre>
</div>`;
                }}
            );
            
            // 插入到页面
            document.getElementById('markdown-content').innerHTML = html;
            
            // 隐藏加载指示器，显示内容
            document.getElementById('loading').style.display = 'none';
            document.getElementById('markdown-content').style.display = 'block';
            
            // 初始化Prism.js语法高亮
            if (typeof Prism !== 'undefined') {{
                setTimeout(() => {{
                    Prism.highlightAll();
                    
                    // 为所有代码块添加行号（如果尚未添加）
                    document.querySelectorAll('pre[class*="language-"]').forEach((block) => {{
                        if (!block.classList.contains('line-numbers')) {{
                            block.classList.add('line-numbers');
                        }}
                    }});
                }}, 100);
            }}
            
            // 为所有图片添加懒加载和错误处理
            document.querySelectorAll('#markdown-content img').forEach((img) => {{
                img.loading = 'lazy';
                img.onerror = function() {{
                    this.alt = '图片加载失败';
                    this.style.border = '1px solid #ff6b6b';
                    this.style.padding = '10px';
                }};
            }});
            
        }} catch (error) {{
            console.error('加载Markdown文件失败:', error);
            
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error-container').style.display = 'block';
            document.getElementById('error-message').textContent = error.message;
            
            // 如果是库加载问题，提供解决方案
            if (error.message.includes('marked') || error.message.includes('库')) {{
                const errorMsg = document.getElementById('error-message');
                errorMsg.innerHTML = error.message + '<br><br>' +
                    '<strong>可能的解决方案：</strong><br>' +
                    '1. 检查网络连接<br>' +
                    '2. 刷新页面重试<br>' +
                    '3. 确保JavaScript没有被浏览器阻止';
            }}
        }}
    }}
    
    // 复制代码功能
    function copyCode(button) {{
        const codeBlock = button.parentElement.nextElementSibling;
        const codeText = codeBlock.textContent;
        
        const textArea = document.createElement('textarea');
        textArea.value = codeText;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        
        textArea.select();
        textArea.setSelectionRange(0, 99999);
        
        let success = false;
        try {{
            success = document.execCommand('copy');
        }} catch (err) {{
            console.error('复制失败:', err);
        }}
        
        document.body.removeChild(textArea);
        
        if (success) {{
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> 已复制';
            button.classList.add('copied');
            
            setTimeout(() => {{
                button.innerHTML = originalText;
                button.classList.remove('copied');
            }}, 2000);
        }} else {{
            // 如果execCommand失败，尝试使用Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(codeText).then(() => {{
                    const originalText = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-check"></i> 已复制';
                    button.classList.add('copied');
                    
                    setTimeout(() => {{
                        button.innerHTML = originalText;
                        button.classList.remove('copied');
                    }}, 2000);
                }}).catch(err => {{
                    console.error('复制失败:', err);
                    button.innerHTML = '<i class="fas fa-times"></i> 复制失败';
                    setTimeout(() => {{
                        button.innerHTML = '<i class="fas fa-copy"></i> 复制代码';
                    }}, 2000);
                }});
            }}
        }}
    }}
    
    // 页面加载后开始检查库状态
    document.addEventListener('DOMContentLoaded', function() {{
        console.log('DOM加载完成，开始检查外部库...');
        
        // 开始检查库加载状态
        checkMarkedLoaded();
        checkPrismLoaded();
        
        // 设置超时检查
        setTimeout(() => {{
            if (!librariesLoaded) {{
                console.warn('库加载超时，尝试继续...');
                // 即使库未完全加载，也尝试继续
                if (typeof marked === 'undefined') {{
                    console.error('marked.js 加载失败，无法渲染Markdown');
                    document.getElementById('loading').innerHTML = 
                        '<i class="fas fa-exclamation-triangle"></i>' +
                        '<p>JavaScript库加载失败</p>' +
                        '<p>请刷新页面或检查网络连接</p>';
                }} else {{
                    // 如果marked已加载但其他库未加载，仍然可以继续
                    librariesLoaded = true;
                    initializeMarked();
                    startLoadingMarkdown();
                }}
            }}
        }}, 10000); // 10秒超时
        
        // 添加键盘快捷键支持
        document.addEventListener('keydown', function(e) {{
            // Ctrl/Cmd + F 搜索
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
                e.preventDefault();
                // 这里可以添加搜索功能
            }}
            
            // Esc 键清除搜索
            if (e.key === 'Escape') {{
                // 这里可以添加清除搜索功能
            }}
        }});
    }});
    
    // 监听网络状态变化
    window.addEventListener('online', function() {{
        console.log('网络已恢复，尝试重新加载内容');
        document.querySelector('.loading-hint').textContent = '检测到网络恢复，正在重新加载...';
        loadAndRenderMarkdown();
    }});
    
    window.addEventListener('offline', function() {{
        console.log('网络断开');
        if (!document.getElementById('markdown-content').innerHTML) {{
            document.querySelector('.loading-hint').textContent = '网络连接已断开，请检查网络连接后刷新页面';
        }}
    }});
    
    // 提供手动重新加载函数
    window.reloadMarkdown = function() {{
        console.log('手动重新加载Markdown');
        loadAndRenderMarkdown();
    }};
    </script>
</body>
</html>'''
    
    # 处理标签
    tags_html = ''
    for tag in post_data.get('tags', []):
        tags_html += f'                <span>{escape(tag)}</span>\n'
    
    # 获取当前年份
    current_year = datetime.now().year
    
    # 将格式化后的内容嵌入到模板中
    full_html = post_template.format(
        title=escape(post_data['title']),
        category=escape(post_data['category']),
        date=post_data['date'],
        reading_time=post_data['reading_time'],
        cover_image=post_data['cover_image'].replace('&amp;', '&'),
        md_filename=md_filename,
        tags=tags_html.rstrip(),
        current_year=current_year
    )
    
    return full_html

def get_excerpt_from_config(post_filename):
    """从 posts-config.json 中提取文章摘要"""
    config_path = 'posts-config.json'
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 查找对应的文章
        for post in config.get('posts', []):
            if post.get('link') == post_filename:
                return post.get('excerpt')
        
        return None
    except (json.JSONDecodeError, Exception):
        return None

def parse_existing_post(post_filename):
    """解析现有文章，提取信息"""
    if not os.path.exists(post_filename):
        return None
    
    # 只处理HTML文件
    with open(post_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    post_data = {'mode': 'dynamic'}  # 所有文章都是动态模式
    
    # 提取标题
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', content)
    if title_match:
        post_data['title'] = unescape(title_match.group(1))
    
    # 提取分类
    category_match = re.search(r'<i class="fas fa-folder"></i>\s*<span>(.*?)</span>', content)
    if category_match:
        post_data['category'] = unescape(category_match.group(1))
    
    # 提取日期
    date_match = re.search(r'<i class="fas fa-calendar-alt"></i>\s*<span>(.*?)</span>', content)
    if date_match:
        post_data['date'] = unescape(date_match.group(1))
    
    # 提取封面图片
    img_match = re.search(r'<img src="(.*?)" alt=', content)
    if img_match:
        post_data['cover_image'] = unescape(img_match.group(1))
    
    # 提取标签
    tags_match = re.search(r'<div class="tag-list">(.*?)</div>', content, re.DOTALL)
    if tags_match:
        tags_html = tags_match.group(1)
        tags = re.findall(r'<span>(.*?)</span>', tags_html)
        post_data['tags'] = [unescape(tag) for tag in tags]
    
    # 从 posts-config.json 提取摘要
    post_data['excerpt'] = get_excerpt_from_config(post_filename)
    
    # 提取文章编号
    match = re.search(r'post(\d+)\.html', post_filename)
    if match:
        post_data['post_number'] = int(match.group(1))
    
    return post_data

def update_posts_config(post_data, post_filename, is_new_post=True):
    """更新 posts-config.json，添加新文章或更新现有文章"""
    config_path = 'posts-config.json'
    
    # 读取现有配置
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"警告: {config_path} 格式错误，将创建新配置")
            config = {"posts": []}
    else:
        print(f"未找到 {config_path}，将创建新配置文件")
        config = {"posts": []}
    
    # 确保 posts 键存在
    if 'posts' not in config:
        config['posts'] = []
    
    # 构建文章配置对象
    post_config = {
        "id": post_data['post_number'],
        "title": post_data['title'],
        "excerpt": post_data['excerpt'],
        "date": post_data['date'],
        "readTime": f"{post_data['reading_time']}分钟",
        "category": post_data['category'],
        "mode": "🔄",
        "image": post_data['cover_image'],
        "link": post_filename
    }
    
    if is_new_post:
        # 新文章：添加到列表开头（最新的文章在最前面）
        config['posts'].insert(0, post_config)
        print(f"✓ 新文章已添加到配置文件顶部")
    else:
        # 更新现有文章
        updated = False
        for i, post in enumerate(config['posts']):
            if post.get('id') == post_data['post_number'] or post.get('link') == post_filename:
                config['posts'][i] = post_config
                updated = True
                print(f"✓ 已更新配置中的文章信息")
                break
        
        if not updated:
            # 如果没找到，作为新文章添加
            config['posts'].insert(0, post_config)
            print(f"✓ 配置中未找到该文章，已作为新文章添加")
    
    # 保存配置文件（带缩进，便于阅读）
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✓ 配置文件已保存: {config_path}")
        print(f"  当前共有 {len(config['posts'])} 篇文章")
        return True
    except Exception as e:
        print(f"✗ 错误: 保存配置文件失败 - {e}")
        return False

def delete_post_from_config(post_filename):
    """从 posts-config.json 中删除文章"""
    config_path = 'posts-config.json'
    
    if not os.path.exists(config_path):
        print(f"警告: 找不到 {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"错误: {config_path} 格式错误")
        return False
    
    # 查找并删除文章
    original_length = len(config['posts'])
    config['posts'] = [post for post in config['posts'] if post.get('link') != post_filename]
    
    if len(config['posts']) < original_length:
        # 保存更新后的配置
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"错误: 保存配置文件失败 - {e}")
            return False
    else:
        print(f"警告: 无法在 {config_path} 中找到文章 {post_filename}")
        return False

def delete_post(post_filename):
    """删除文章页面"""
    if not os.path.exists(post_filename):
        print(f"错误: 找不到文件 {post_filename}")
        return False
    
    try:
        existing_data = parse_existing_post(post_filename)
        title = existing_data.get('title', '未知标题') if existing_data else '未知标题'
        print(f"\n将要删除文章: {post_filename}")
        print(f"标题: {title}")
        confirm = input("确认删除? (y/n，默认: n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return False
    except:
        confirm = input(f"\n确认删除 {post_filename}? (y/n，默认: n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return False
    
    # 从 posts-config.json 中删除
    print("正在从 posts-config.json 中删除...")
    delete_post_from_config(post_filename)
    
    # 删除HTML文件
    try:
        os.remove(post_filename)
        print(f"✓ 已删除文件: {post_filename}")
        
        # 删除对应的Markdown文件
        md_file = post_filename.replace('.html', '.md')
        if os.path.exists(md_file):
            os.remove(md_file)
            print(f"✓ 已删除Markdown文件: {md_file}")
        
        return True
    except Exception as e:
        print(f"✗ 删除文件失败: {e}")
        return False

def list_all_posts():
    """列出所有文章及其在配置中的状态"""
    config_path = 'posts-config.json'
    
    # 读取配置文件
    config_posts = []
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                config_posts = config.get('posts', [])
        except:
            pass
    
    print("\n" + "=" * 80)
    print("当前博客文章列表")
    print("=" * 80)
    
    if not config_posts:
        print("暂无文章（posts-config.json 为空或不存在）")
        print("\n提示: 使用选项 1 从 Markdown 文件生成新文章")
        print("      或使用选项 4 自动扫描现有文章")
    else:
        print(f"共有 {len(config_posts)} 篇文章:\n")
        for i, post in enumerate(config_posts, 1):
            print(f"{i}. [{post.get('id', '?')}] {post.get('title', '无标题')}")
            print(f"   文件: {post.get('link', '未知')}")
            print(f"   分类: {post.get('category', '未分类')} | 日期: {post.get('date', '未知')}")
            print(f"   阅读时间: {post.get('readTime', '未知')} | 模式: {post.get('mode', '🔄')}")
            
            # 检查文件是否存在
            link = post.get('link', '')
            if link:
                html_exists = os.path.exists(link)
                md_file = link.replace('.html', '.md')
                md_exists = os.path.exists(md_file)
                
                status = []
                if html_exists:
                    status.append("✓ HTML")
                else:
                    status.append("✗ HTML缺失")
                
                if md_exists:
                    status.append("✓ MD")
                else:
                    status.append("✗ MD缺失")
                
                print(f"   状态: {' | '.join(status)}")
            print()
    
    print("=" * 80)

def sync_all_posts():
    """扫描所有文章文件并同步到配置文件"""
    print("\n" + "=" * 80)
    print("扫描并同步所有文章到 posts-config.json")
    print("=" * 80)
    
    # 获取所有文章文件
    post_files = get_all_post_files()
    
    if not post_files:
        print("\n未找到任何文章文件 (post*.html)")
        print("提示: 使用选项 1 从 Markdown 文件生成新文章")
        return
    
    print(f"\n找到 {len(post_files)} 个文章文件:")
    for f in post_files:
        print(f"  • {f}")
    
    confirm = input(f"\n是否将这些文章同步到 posts-config.json? (y/n，默认: y): ").strip().lower()
    if confirm == 'n':
        print("操作已取消")
        return
    
    # 读取或创建配置
    config_path = 'posts-config.json'
    config = {"posts": []}
    
    print("\n开始同步...")
    synced_count = 0
    error_count = 0
    
    for post_file in post_files:
        try:
            print(f"\n处理: {post_file}")
            post_data = parse_existing_post(post_file)
            
            if not post_data:
                print(f"  ✗ 无法解析文章信息")
                error_count += 1
                continue
            
            # 构建配置对象
            post_config = {
                "id": post_data.get('post_number', 0),
                "title": post_data.get('title', '无标题'),
                "excerpt": post_data.get('excerpt', '暂无摘要'),
                "date": post_data.get('date', datetime.now().strftime("%Y年%m月%d日")),
                "readTime": "5分钟",  # 默认值
                "category": post_data.get('category', '未分类'),
                "mode": "🔄",
                "image": post_data.get('cover_image', 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80'),
                "link": post_file
            }
            
            config['posts'].append(post_config)
            print(f"  ✓ 已添加: {post_data.get('title', '无标题')}")
            synced_count += 1
            
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            error_count += 1
    
    # 按ID倒序排序（最新的在前）
    config['posts'].sort(key=lambda x: x.get('id', 0), reverse=True)
    
    # 保存配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 80)
        print("✓ 同步完成！")
        print("=" * 80)
        print(f"成功同步: {synced_count} 篇文章")
        if error_count > 0:
            print(f"失败: {error_count} 篇文章")
        print(f"配置文件: {config_path}")
        print("\n提示: 刷新 index.html 即可看到所有文章")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 保存配置文件失败: {e}")

def main():
    """主函数"""
    try:
        print("=" * 80)
        print("博客文章管理工具 - 动态加载版")
        print("支持从 Markdown 动态解析，自动更新 posts-config.json")
        print("=" * 80)
        print()
        print("请选择操作:")
        print("1. 从 Markdown 文件生成/更新文章")
        print("2. 删除文章")
        print("3. 查看所有文章列表")
        print("4. 扫描并同步所有文章到配置文件")
        print()
        
        operation = input("请选择 (1/2/3/4，默认: 1): ").strip() or "1"
        
        if operation == "3":
            list_all_posts()
            return
        
        if operation == "4":
            sync_all_posts()
            return
        
        if operation == "2":
            post_files = get_all_post_files()
            if not post_files:
                print("没有找到文章文件")
                return
            
            print("\n现有文章列表:")
            for i, f in enumerate(post_files, 1):
                try:
                    data = parse_existing_post(f)
                    title = data.get('title', '未知标题') if data else '未知标题'
                    mode_text = '🔄动态模式'
                    print(f"  {i}. {f} - {title} [{mode_text}]")
                except:
                    print(f"  {i}. {f}")
            
            print()
            file_choice = input(f"请选择要删除的文章 (1-{len(post_files)}): ").strip()
            try:
                file_index = int(file_choice) - 1
                if 0 <= file_index < len(post_files):
                    post_filename = post_files[file_index]
                    if delete_post(post_filename):
                        print("\n" + "=" * 60)
                        print("删除完成！")
                        print("=" * 60)
                else:
                    print("无效选择")
            except ValueError:
                print("无效输入")
            return
        
        # 从 Markdown 文件生成/更新文章
        md_file_path = None
        
        if len(sys.argv) > 1:
            md_file_path = sys.argv[1]
        else:
            md_files = [f for f in os.listdir('.') if f.endswith('.md')]
            if md_files:
                print("\n找到以下 Markdown 文件:")
                for i, f in enumerate(md_files, 1):
                    print(f"  {i}. {f}")
                print()
                file_choice = input(f"请选择文件 (1-{len(md_files)})，或直接输入文件路径: ").strip()
                
                try:
                    file_index = int(file_choice) - 1
                    if 0 <= file_index < len(md_files):
                        md_file_path = md_files[file_index]
                    else:
                        md_file_path = file_choice
                except ValueError:
                    md_file_path = file_choice
            else:
                md_file_path = input("\n请输入 Markdown 文件路径: ").strip()
        
        if not md_file_path:
            print("错误: 未指定 Markdown 文件")
            return
        
        print(f"\n正在读取: {md_file_path}...")
        post_data = parse_markdown_file(md_file_path)
        if not post_data:
            return
        
        print(f"标题: {post_data['title']}")
        print(f"分类: {post_data['category']}")
        print(f"日期: {post_data['date']}")
        print(f"模式: 动态解析模式")
        
        # 检查是否要编辑现有文章
        post_files = get_all_post_files()
        existing_post = None
        
        for post_file in post_files:
            try:
                existing_data = parse_existing_post(post_file)
                if existing_data and existing_data.get('title') == post_data['title']:
                    existing_post = post_file
                    break
            except:
                continue
        
        is_new_post = True
        post_filename = None
        
        if existing_post:
            print(f"\n找到同名文章: {existing_post}")
            update_choice = input("是否更新现有文章? (y/n，默认: y): ").strip().lower()
            if update_choice != 'n':
                post_filename = existing_post
                match = re.search(r'post(\d+)\.html', post_filename)
                if match:
                    post_data['post_number'] = int(match.group(1))
                is_new_post = False
            else:
                is_new_post = True
        
        if is_new_post:
            post_data['post_number'] = get_next_post_number()
            post_filename = f"post{post_data['post_number']}.html"
        
        # 生成文章 HTML
        action = "更新" if not is_new_post else "生成"
        print(f"\n正在{action}文章: {post_filename}...")
        
        # 复制Markdown文件并重命名
        md_target = f"post{post_data['post_number']}.md"
        if md_file_path != md_target:
            shutil.copy2(md_file_path, md_target)
            print(f"✓ 已复制Markdown文件: {md_target}")
        
        html_content = create_post_html(post_data, post_filename)
        
        # 保存文章文件
        with open(post_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ 文章已保存: {post_filename}")
        
        # 更新 posts-config.json
        print("\n正在更新 posts-config.json...")
        if update_posts_config(post_data, post_filename, is_new_post=is_new_post):
            action_text = "更新" if not is_new_post else "添加"
            print(f"\n✓ 文章已成功{action_text}到配置文件")
        else:
            print("\n✗ 更新 posts-config.json 失败")
        
        print("\n" + "=" * 80)
        print("✓ 完成！文章已生成并配置")
        print("=" * 80)
        print(f"\n生成的文件:")
        print(f"  • HTML文件: {post_filename}")
        print(f"  • Markdown源文件: {md_target}")
        print(f"  • 配置文件: posts-config.json (已自动更新)")
        
        print(f"\n文章信息:")
        print(f"  • 标题: {post_data['title']}")
        print(f"  • 分类: {post_data['category']}")
        print(f"  • 日期: {post_data['date']}")
        print(f"  • 阅读时间: {post_data['reading_time']} 分钟")
        print(f"  • 编号: #{post_data['post_number']}")
        
        print(f"\n动态加载说明:")
        print(f"  ✓ 文章内容从 Markdown 文件动态加载")
        print(f"  ✓ 修改文章只需编辑 {md_target}")
        print(f"  ✓ 页面会自动重新加载更新后的内容")
        print(f"  ✓ index.html 会自动从 posts-config.json 读取文章列表")
        print(f"  ✓ 支持代码高亮、复制功能、响应式设计")
        
        print(f"\n下一步:")
        print(f"  1. 在浏览器中打开 index.html 查看博客首页")
        print(f"  2. 点击文章卡片查看 {post_filename}")
        print(f"  3. 编辑 {md_target} 修改文章内容")
        print(f"  4. 刷新页面即可看到更新")
        
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()