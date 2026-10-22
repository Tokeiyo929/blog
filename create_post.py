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

POST_FILE_PATTERN = re.compile(r'^post(\d+)\.html$')
CONFIG_PATH = 'posts-config.json'
DEFAULT_COVER_IMAGE = "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80"

def configure_stdio():
    """让 Windows 控制台也能稳定输出中文和图标"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')

def extract_post_number(filename):
    """从文章文件名中提取编号"""
    match = POST_FILE_PATTERN.match(os.path.basename(filename))
    return int(match.group(1)) if match else None

def new_posts_config():
    """创建空的文章配置，避免共享可变默认值"""
    return {"posts": []}

def get_all_post_files():
    """获取所有文章文件列表"""
    html_files = [f for f in os.listdir('.') if extract_post_number(f) is not None]
    html_files.sort(key=extract_post_number)
    return html_files

def get_next_post_number():
    """获取下一个文章编号"""
    post_files = get_all_post_files()
    if not post_files:
        return 1

    numbers = [extract_post_number(f) for f in post_files]
    return max(numbers) + 1 if numbers else 1

def load_posts_config(config_path=CONFIG_PATH, warn=True):
    """读取 posts-config.json，缺失或损坏时返回默认结构"""
    if not os.path.exists(config_path):
        if warn:
            print(f"未找到 {config_path}，将创建新配置文件")
        return new_posts_config()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        if warn:
            print(f"警告: {config_path} 格式错误，将创建新配置")
        return new_posts_config()

    if not isinstance(config, dict):
        return new_posts_config()

    posts = config.get('posts')
    if not isinstance(posts, list):
        config['posts'] = []
    return config

def save_posts_config(config, config_path=CONFIG_PATH):
    """保存 posts-config.json"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def build_post_config(post_data, post_filename):
    """构建首页使用的文章配置对象"""
    return {
        "id": post_data.get('post_number', 0),
        "title": post_data.get('title', '无标题'),
        "excerpt": post_data.get('excerpt') or '暂无摘要',
        "date": post_data.get('date', datetime.now().strftime("%Y年%m月%d日")),
        "readTime": f"{post_data.get('reading_time', 5)}分钟",
        "category": post_data.get('category', '未分类'),
        "mode": "🔄",
        "image": post_data.get('cover_image', DEFAULT_COVER_IMAGE),
        "link": post_filename
    }

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
        post_data['cover_image'] = DEFAULT_COVER_IMAGE
    
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
    """生成文章页；共享行为放在 post.js，共享样式放在 post.css。"""
    md_filename = post_filename.replace('.html', '.md')
    title = escape(str(post_data.get('title', '无标题')), quote=True)
    date = escape(str(post_data.get('date', '')), quote=True)
    cover_image = escape(str(post_data.get('cover_image', DEFAULT_COVER_IMAGE)), quote=True)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'self'; object-src 'none'; form-action 'self'; script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com data:; img-src 'self' https: data:; connect-src 'self' https://cdn.jsdelivr.net; upgrade-insecure-requests">
    <title>{title}</title>
    <link rel="icon" href="favicon.svg" type="image/svg+xml">
    <link rel="preconnect" href="https://cdnjs.cloudflare.com" crossorigin>
    <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
    <link rel="preconnect" href="https://images.unsplash.com">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" integrity="sha384-iw3OoTErCYJJB9mCa8LNS2hbsQ7M3C0EpIsO/H5+EGAkPGc6rk+V8i04oW/K5xq0" crossorigin="anonymous">
    <script defer src="https://cdn.jsdelivr.net/npm/marked@18.0.5/lib/marked.umd.js" integrity="sha384-ZD0fTOwPMHi7zM6WTVIWJR21I07lq0ccnqz3J6WMvQKG9thh4y7TA1QE6PJu0Af8" crossorigin="anonymous"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/dompurify@3.4.10/dist/purify.min.js" integrity="sha384-eguRoJERj8ghOpzO//Rl7+ScQsQIR1cH+ajll7+fG+IpbNPlkZsQn9h8ccr+wPXx" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" integrity="sha384-wFjoQjtV1y5jVHbt0p35Ui8aV8GVpEZkyF99OXWqP/eNJDU93D3Ugxkoyh6Y2I4A" crossorigin="anonymous">
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js" integrity="sha384-06z5D//U/xpvxZHuUz92xBvq3DqBBFi7Up53HRrbV7Jlv7Yvh/MZ7oenfUe9iCEt" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js" integrity="sha384-WJdEkJKrbsqw0evQ4GB6mlsKe5cGTxBOw4KAEIa52ZLB7DDpliGkwdme/HMa5n1m" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js" integrity="sha384-D44bgYYKvaiDh4cOGlj1dbSDpSctn2FSUj118HZGmZEShZcO2v//Q5vvhNy206pp" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js" integrity="sha384-0mV13Neu0xhJFyl+HV43C+XiR13bGSeL7D0/7e6hK7sJgvyvK6HVjeQwmvXTstY" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js" integrity="sha384-9WmlN8ABpoFSSHvBGGjhvB3E/D8UkNB9HpLJjBQFC2VSQsM1odiQDv4NbEo+7l15" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js" integrity="sha384-RhrmFFMb0ZCHImjFMpR/UE3VEtIVTCtNrtKqXQCzqXZNJala02N3UbVhi+qzw3CY" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markdown.min.js" integrity="sha384-s888ApkYHxfPsp8n81g77Unl/0XYnYltLvWbwqKHcheRE8/dZPlT4IjW3mRGv/Hd" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-yaml.min.js" integrity="sha384-AKAiycghK0jDCjD+aavMHzDkLzRR7Yzcwh3+xL/295cvyVMe+cxQfyQC8xxGGcI8" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-csharp.min.js" integrity="sha384-nMKYzg6yfy0qgpaRpVhHvZp0gT5sgvmZYlFC0XAKZSp+zFUB9rE6zsdmIEiou4bV" crossorigin="anonymous"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js" integrity="sha384-6QJu8apxMmB9TiPVWzYKF5pRgKcz7snO0/QU+MrWmgBLECQjoa6erxX2VQ5t41Jd" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" integrity="sha384-nUkTNLI8COlMCRJ0FHIdX76If83145OTCLUx4gQyfnO0gGeO/sD9czGEUBxtkcUv" crossorigin="anonymous">
    <link rel="stylesheet" href="art-theme-2.css">
    <link rel="stylesheet" href="post.css">
    <script defer src="post.js"></script>
</head>
<body data-markdown="{md_filename}">
    <main class="container">
        <article>
            <header class="article-header">
                <h1 class="article-title">{title}</h1>
                <div class="article-meta">
                    <div class="article-meta-item">
                        <i class="fas fa-calendar-alt" aria-hidden="true"></i>
                        <span>{date}</span>
                    </div>
                </div>
            </header>
            <div class="article-cover">
                <img src="{cover_image}" alt="{title}" width="1170" height="780" loading="eager" fetchpriority="high">
            </div>
            <div class="loading-indicator" id="loading">
                <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
                <p>正在加载文章内容...</p>
            </div>
            <div class="error-container" id="error-container" hidden>
                <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                <h3>内容加载失败</h3>
                <p id="error-message">未知错误</p>
                <button type="button" id="retry-load" class="copy-button">
                    <i class="fas fa-redo" aria-hidden="true"></i> 重试加载
                </button>
            </div>
            <div class="markdown-content" id="markdown-content" hidden></div>
        </article>
    </main>
    <a href="index.html#blog" class="side-back" aria-label="返回博客列表">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        <span>返回列表</span>
    </a>
</body>
</html>
'''

def get_excerpt_from_config(post_filename):
    """从 posts-config.json 中提取文章摘要"""
    config = load_posts_config(warn=False)
    for post in config.get('posts', []):
        if post.get('link') == post_filename:
            return post.get('excerpt')
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
    post_number = extract_post_number(post_filename)
    if post_number is not None:
        post_data['post_number'] = post_number

    return post_data

def update_posts_config(post_data, post_filename, is_new_post=True):
    """更新 posts-config.json，添加新文章或更新现有文章"""
    config = load_posts_config()
    post_config = build_post_config(post_data, post_filename)

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
        save_posts_config(config)
        print(f"✓ 配置文件已保存: {CONFIG_PATH}")
        print(f"  当前共有 {len(config['posts'])} 篇文章")
        return True
    except Exception as e:
        print(f"✗ 错误: 保存配置文件失败 - {e}")
        return False

def delete_post_from_config(post_filename):
    """从 posts-config.json 中删除文章"""
    if not os.path.exists(CONFIG_PATH):
        print(f"警告: 找不到 {CONFIG_PATH}")
        return False

    config = load_posts_config()

    # 查找并删除文章
    original_length = len(config['posts'])
    config['posts'] = [post for post in config['posts'] if post.get('link') != post_filename]
    
    if len(config['posts']) < original_length:
        # 保存更新后的配置
        try:
            save_posts_config(config)
            return True
        except Exception as e:
            print(f"错误: 保存配置文件失败 - {e}")
            return False
    else:
        print(f"警告: 无法在 {CONFIG_PATH} 中找到文章 {post_filename}")
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
    except Exception:
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
    config_posts = load_posts_config(warn=False).get('posts', [])
    
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
            
            md_file = post_file.replace('.html', '.md')
            if os.path.exists(md_file):
                md_data = parse_markdown_file(md_file)
                if md_data:
                    post_data.update({
                        'excerpt': md_data.get('excerpt', post_data.get('excerpt')),
                        'reading_time': md_data.get('reading_time', 5),
                    })
            post_data.setdefault('reading_time', 5)
            post_config = build_post_config(post_data, post_file)
            
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
        save_posts_config(config)
        
        print("\n" + "=" * 80)
        print("✓ 同步完成！")
        print("=" * 80)
        print(f"成功同步: {synced_count} 篇文章")
        if error_count > 0:
            print(f"失败: {error_count} 篇文章")
        print(f"配置文件: {CONFIG_PATH}")
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
                except Exception:
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
            except Exception:
                continue
        
        is_new_post = True
        post_filename = None
        
        if existing_post:
            print(f"\n找到同名文章: {existing_post}")
            update_choice = input("是否更新现有文章? (y/n，默认: y): ").strip().lower()
            if update_choice != 'n':
                post_filename = existing_post
                post_number = extract_post_number(post_filename)
                if post_number is not None:
                    post_data['post_number'] = post_number
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
    configure_stdio()
    main()
