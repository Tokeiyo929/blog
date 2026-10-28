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
BLOG_CONFIG_PATH = 'blog_config.json'

with open(BLOG_CONFIG_PATH, 'r', encoding='utf-8') as config_file:
    BLOG_CONFIG = json.load(config_file)

DEFAULT_CATEGORY = BLOG_CONFIG['default_category']
EXCERPT_LENGTH = BLOG_CONFIG['excerpt_length']
SUPPORTED_LANGUAGES = BLOG_CONFIG['supported_languages']

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
    return max((extract_post_number(f) for f in get_all_post_files()), default=0) + 1

def load_posts_config(config_path=CONFIG_PATH, warn=True):
    """读取 posts-config.json，缺失或损坏时返回默认结构"""
    if not os.path.exists(config_path):
        if warn:
            print(f"未找到 {config_path}，将创建新配置文件")
        return new_posts_config()

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    if not isinstance(config, dict):
        raise ValueError(f'{config_path} must contain an object')

    posts = config.get('posts')
    if not isinstance(posts, list):
        raise ValueError(f'{config_path}.posts must be a list')
    return config

def save_posts_config(config, config_path=CONFIG_PATH):
    """保存 posts-config.json"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_config_post(post_number):
    if post_number is None:
        return None
    return next(
        (post for post in load_posts_config(warn=False).get('posts', [])
         if post.get('id') == post_number),
        None,
    )

def build_post_config(post_data, post_filename):
    """构建首页使用的文章配置对象"""
    post_config = {
        "id": post_data.get('post_number', 0),
        "title": post_data.get('title', '无标题'),
        "excerpt": post_data.get('excerpt') or extract_excerpt(post_data.get('content', '')),
        "date": post_data.get('date', datetime.now().strftime("%Y年%m月%d日")),
        "category": post_data.get('category', DEFAULT_CATEGORY),
        "project": post_data.get('project', ''),
        "link": post_filename
    }
    if post_data.get('image'):
        post_config['image'] = post_data['image']
    return post_config

def extract_excerpt(content):
    for line in content.splitlines():
        text = line.strip()
        if not text or text.startswith(('#', '```', '![', '-', '>', '|')):
            continue
        text = re.sub(r'!\[[^]]*\]\([^)]*\)', '', text)
        text = re.sub(r'\[([^]]*)\]\([^)]*\)', r'\1', text)
        text = re.sub(r'[*`~]', '', text).strip()
        if text:
            return text[:EXCERPT_LENGTH] + ('…' if len(text) > EXCERPT_LENGTH else '')
    return ''

def extract_first_image(content):
    match = re.search(r'!\[[^]]*\]\(([^)\s]+)', content)
    return match.group(1) if match else None

def parse_markdown_file(md_file_path):
    """解析 Markdown 文件，提取元数据和内容"""
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read().lstrip('\ufeff')
    
    post_data = {'content': content.strip()}
    
    # 检查是否有 YAML front matter
    front_matter_match = re.match(
        r'^---\s*\n((?:[A-Za-z_][\w-]*\s*:[^\r\n]*\r?\n)+)---\s*\n(.*)$',
        content,
        re.DOTALL,
    )
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
                    post_data['image'] = value
                elif key == 'project':
                    post_data['project'] = value
    else:
        # 没有 front matter，使用文件名和默认值
        # 从文件名提取标题（去掉扩展名）
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        post_data['title'] = base_name
    
    # 设置默认值
    if 'title' not in post_data or not post_data['title']:
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        post_data['title'] = base_name
    
    if 'category' not in post_data:
        post_data['category'] = DEFAULT_CATEGORY
    
    if 'date' not in post_data:
        post_data['date'] = datetime.now().strftime("%Y年%m月%d日")
    
    post_number = extract_post_number(os.path.basename(md_file_path).replace('.md', '.html'))
    post_data['post_number'] = post_number
    config_post = get_config_post(post_number)
    if config_post:
        for key in ('title', 'date', 'category', 'project'):
            if not front_matter_match or key not in post_data:
                post_data[key] = config_post.get(key, '')

    post_data.setdefault('project', '')
    post_data['image'] = post_data.get('image') or extract_first_image(post_data['content'])
    
    return post_data

def create_post_html(post_data, post_filename):
    """生成文章页；共享行为放在 post.js，共享样式放在 post.css。"""
    md_filename = post_filename.replace('.html', '.md')
    title = escape(str(post_data.get('title', '无标题')), quote=True)
    date = escape(str(post_data.get('date', '')), quote=True)
    prism_languages = '\n'.join(
        f'    <script defer src="vendor/prism/components/prism-{language}.min.js"></script>'
        for language in SUPPORTED_LANGUAGES
    )

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'self'; object-src 'none'; form-action 'self'; script-src 'self'; style-src 'self'; font-src 'self' data:; img-src 'self' https: data:; connect-src 'self'; upgrade-insecure-requests">
    <title>{title}</title>
    <link rel="icon" href="favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="vendor/fontawesome/all.min.css">
    <script defer src="vendor/marked.umd.js"></script>
    <script defer src="vendor/purify.min.js"></script>
    <link rel="stylesheet" href="vendor/prism/themes/prism-tomorrow.min.css">
    <script defer src="vendor/prism/prism.min.js"></script>
{prism_languages}
    <script defer src="vendor/prism/plugins/line-numbers/prism-line-numbers.min.js"></script>
    <link rel="stylesheet" href="vendor/prism/plugins/line-numbers/prism-line-numbers.min.css">
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

def parse_existing_post(post_filename):
    """解析现有文章，提取信息"""
    if not os.path.exists(post_filename):
        return None
    
    # 只处理HTML文件
    with open(post_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    post_data = {}
    
    # 提取标题
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', content)
    if title_match:
        post_data['title'] = unescape(title_match.group(1))
    
    # 提取日期
    date_match = re.search(r'<i class="fas fa-calendar-alt"></i>\s*<span>(.*?)</span>', content)
    if date_match:
        post_data['date'] = unescape(date_match.group(1))
    
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
    
    existing_data = parse_existing_post(post_filename)
    title = existing_data.get('title', '未知标题')
    print(f"\n将要删除文章: {post_filename}")
    print(f"标题: {title}")
    confirm = input("确认删除? (y/n，默认: n): ").strip().lower()
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
            print(f"   分类: {post.get('category', DEFAULT_CATEGORY)} | 日期: {post.get('date', '未知')}")
            if post.get('project'):
                print(f"   项目: {post['project']}")
            
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
                post_data.update(parse_markdown_file(md_file))
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
                    print(f"  {i}. {f} - {title}")
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
