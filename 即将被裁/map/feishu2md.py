import time
import json
import os
import re
import logging
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeishuWikiManualScraper:
    def __init__(self):
        self.driver = None
        self.target_url = "https://os3tzyabw2.feishu.cn/docs/doccn5ww9eRUP9MBCxTwvwFz7Ne?refer_index=1&refer_type=citation"
        self.wait = None
        self.all_content = []
        self.all_images = []
        self.scroll_sessions = []
        self.image_counter = 0  # 用于生成唯一文件名
        
    def init_driver(self):
        """初始化浏览器驱动"""
        try:
            chromedriver_path = "chromedriver.exe"
            if not os.path.exists(chromedriver_path):
                logger.error(f"未在当前目录找到 {chromedriver_path}")
                logger.info("请确保 chromedriver.exe 在当前目录下")
                return False
            
            chrome_options = Options()
            
            # 禁用自动化控制标志
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 基本设置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 添加用户代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 禁用自动化特征
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 重要：允许下载Blob URL
            prefs = {
                "download.default_directory": os.path.abspath("feishu_wiki_manual/images"),
                "download.prompt_for_download": False,
                "directory_upgrade": True,
                "safebrowsing.enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 创建服务
            service = Service(executable_path=chromedriver_path)
            
            # 初始化驱动
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置显式等待
            self.wait = WebDriverWait(self.driver, 30)
            
            # 执行JavaScript来修改navigator属性
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            """)
            
            logger.info("浏览器驱动初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"浏览器驱动初始化失败: {e}")
            return False
    
    def access_and_login(self):
        """访问页面并等待登录"""
        print("\n" + "="*60)
        print("正在访问目标页面...")
        print(f"URL: {self.target_url}")
        print("="*60 + "\n")
        
        try:
            self.driver.get(self.target_url)
            time.sleep(3)
            
            print("\n" + "="*60)
            print("请扫描页面上的二维码登录飞书")
            print("登录成功后，程序会自动开始爬取内容...")
            print("="*60 + "\n")
            
            # 等待登录成功
            logger.info("等待登录...")
            
            for i in range(90):
                current_url = self.driver.current_url
                
                if i % 10 == 0:
                    print(f"等待登录... {i*2}秒")
                
                # 检查是否还在登录页面
                if 'account' in current_url or 'login' in current_url or 'passport' in current_url:
                    time.sleep(2)
                    continue
                else:
                    # 等待页面加载
                    time.sleep(5)
                    
                    # 检查是否能看到wiki内容
                    try:
                        wiki_elements = self.driver.find_elements(By.CSS_SELECTOR, '.ace-line, .docx-text-block, .docx-image-block')
                        if wiki_elements:
                            print("✓ 登录成功！检测到Wiki内容")
                            return True
                    except:
                        pass
                    
                    time.sleep(2)
                    continue
            
            print("⚠ 登录检测超时，尝试继续...")
            return True
            
        except Exception as e:
            logger.error(f"访问页面失败: {e}")
            return False
    
    def extract_current_view_content(self):
        """提取当前可视区域的内容（包括文本和图片）"""
        try:
            # 获取当前滚动位置
            current_scroll = self.driver.execute_script("return window.pageYOffset;")
            window_height = self.driver.execute_script("return window.innerHeight;")
            
            # 提取当前可视区域的内容
            content_data = self.driver.execute_script("""
                // 获取当前滚动位置和窗口高度
                const currentScroll = window.pageYOffset;
                const windowHeight = window.innerHeight;
                const viewportTop = currentScroll;
                const viewportBottom = currentScroll + windowHeight;
                
                // 收集所有内容元素：文本块和图片
                const textElements = document.querySelectorAll('.ace-line');
                const imageElements = document.querySelectorAll('.docx-image-block img, .docx-image, img[src^="blob:"]');
                
                console.log(`当前找到 ${textElements.length} 个文本元素`);
                console.log(`当前找到 ${imageElements.length} 个图片元素`);
                
                const linesData = [];
                const imagesData = [];
                let visibleLines = 0;
                let visibleImages = 0;
                
                // 处理文本元素
                textElements.forEach((line, index) => {
                    // 获取元素位置
                    const rect = line.getBoundingClientRect();
                    const elementTop = rect.top + currentScroll;
                    const elementBottom = rect.bottom + currentScroll;
                    
                    // 检查元素是否在可视区域内
                    const isInViewport = (
                        (elementTop >= viewportTop && elementTop <= viewportBottom) ||
                        (elementBottom >= viewportTop && elementBottom <= viewportBottom) ||
                        (elementTop <= viewportTop && elementBottom >= viewportBottom)
                    );
                    
                    const text = line.textContent || line.innerText || '';
                    const trimmed = text.trim();
                    
                    if (trimmed && trimmed.length > 0) {
                        // 获取元素路径（简化版）
                        let elementPath = '';
                        try {
                            let current = line;
                            let depth = 0;
                            while (current && current !== document.body && depth < 5) {
                                const tag = current.tagName.toLowerCase();
                                const id = current.id ? '#' + current.id : '';
                                const className = current.className ? '.' + current.className.split(' ')[0] : '';
                                elementPath = tag + id + className + ' > ' + elementPath;
                                current = current.parentElement;
                                depth++;
                            }
                        } catch (e) {
                            elementPath = 'unknown';
                        }
                        
                        // 分析元素类型
                        let blockType = 'paragraph';
                        let headingLevel = 0;
                        let isList = false;
                        let listType = '';
                        let listLevel = 0;
                        let isCode = false;
                        
                        // 检查父元素结构
                        let parent = line.parentElement;
                        let level = 0;
                        
                        while (parent && level < 5) {
                            const className = parent.className || '';
                            
                            // 检查标题
                            if (className.includes('heading-h1')) {
                                blockType = 'h1';
                                headingLevel = 1;
                                break;
                            } else if (className.includes('heading-h2')) {
                                blockType = 'h2';
                                headingLevel = 2;
                                break;
                            } else if (className.includes('heading-h3')) {
                                blockType = 'h3';
                                headingLevel = 3;
                                break;
                            } else if (className.includes('heading-h4')) {
                                blockType = 'h4';
                                headingLevel = 4;
                                break;
                            }
                            
                            // 检查列表
                            if (className.includes('ordered-list')) {
                                isList = true;
                                listType = 'ordered';
                                break;
                            } else if (className.includes('bullet-list')) {
                                isList = true;
                                listType = 'bullet';
                                break;
                            }
                            
                            // 检查代码
                            if (line.querySelector('.inline-code')) {
                                isCode = true;
                                break;
                            }
                            
                            parent = parent.parentElement;
                            level++;
                        }
                        
                        linesData.push({
                            elementType: 'text',
                            index: index,
                            text: trimmed,
                            blockType: blockType,
                            headingLevel: headingLevel,
                            isList: isList,
                            listType: listType,
                            listLevel: listLevel,
                            isCode: isCode,
                            elementPath: elementPath.substring(0, 100),
                            isInViewport: isInViewport,
                            elementTop: Math.round(elementTop),
                            elementBottom: Math.round(elementBottom)
                        });
                        
                        if (isInViewport) {
                            visibleLines++;
                        }
                    }
                });
                
                // 处理图片元素
                imageElements.forEach((img, index) => {
                    // 获取元素位置
                    const rect = img.getBoundingClientRect();
                    const elementTop = rect.top + currentScroll;
                    const elementBottom = rect.bottom + currentScroll;
                    
                    // 检查元素是否在可视区域内
                    const isInViewport = (
                        (elementTop >= viewportTop && elementTop <= viewportBottom) ||
                        (elementBottom >= viewportTop && elementBottom <= viewportBottom) ||
                        (elementTop <= viewportTop && elementBottom >= viewportBottom)
                    );
                    
                    const src = img.src || '';
                    const alt = img.alt || '图片';
                    
                    if (src) {
                        // 获取图片容器信息
                        const container = img.closest('.docx-image-block, .image-block, .image-block-container');
                        const containerClass = container ? container.className : '';
                        
                        // 获取图片尺寸
                        const naturalWidth = img.naturalWidth || 0;
                        const naturalHeight = img.naturalHeight || 0;
                        const displayWidth = img.width || 0;
                        const displayHeight = img.height || 0;
                        
                        // 获取图片描述（如果有）
                        let description = '';
                        try {
                            const figcaption = img.closest('figure')?.querySelector('figcaption');
                            if (figcaption) {
                                description = figcaption.textContent || '';
                            }
                        } catch (e) {}
                        
                        imagesData.push({
                            elementType: 'image',
                            index: index,
                            src: src,
                            alt: alt,
                            description: description,
                            naturalWidth: naturalWidth,
                            naturalHeight: naturalHeight,
                            displayWidth: displayWidth,
                            displayHeight: displayHeight,
                            containerClass: containerClass.substring(0, 50),
                            isInViewport: isInViewport,
                            elementTop: Math.round(elementTop),
                            elementBottom: Math.round(elementBottom),
                            isBlobUrl: src.startsWith('blob:')
                        });
                        
                        if (isInViewport) {
                            visibleImages++;
                        }
                    }
                });
                
                return {
                    totalLines: linesData.length,
                    visibleLines: visibleLines,
                    totalImages: imagesData.length,
                    visibleImages: visibleImages,
                    scrollPosition: currentScroll,
                    windowHeight: windowHeight,
                    lines: linesData,
                    images: imagesData
                };
            """)
            
            return content_data
            
        except Exception as e:
            logger.error(f"提取内容失败: {e}")
            return None
    
    def download_blob_image(self, blob_url, filename):
        """使用JavaScript下载Blob URL图片"""
        try:
            # 创建图片保存目录
            image_dir = 'feishu_wiki_manual/images'
            os.makedirs(image_dir, exist_ok=True)
            
            # 生成完整的文件路径
            filepath = os.path.join(image_dir, filename)
            
            # 如果图片已经存在，跳过下载
            if os.path.exists(filepath):
                print(f"  图片已存在: {filename}")
                return filepath
            
            print(f"  下载Blob图片: {filename}")
            
            # 使用JavaScript将Blob URL转换为base64并下载
            base64_data = self.driver.execute_script("""
                // 将Blob URL转换为base64
                return new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('GET', arguments[0], true);
                    xhr.responseType = 'blob';
                    
                    xhr.onload = function() {
                        if (xhr.status === 200) {
                            const blob = xhr.response;
                            const reader = new FileReader();
                            
                            reader.onloadend = function() {
                                // 获取base64数据
                                const base64data = reader.result;
                                // 提取纯base64部分
                                const base64 = base64data.split(',')[1];
                                resolve({
                                    base64: base64,
                                    mimeType: blob.type,
                                    size: blob.size
                                });
                            };
                            
                            reader.onerror = function() {
                                reject(new Error('FileReader读取失败'));
                            };
                            
                            reader.readAsDataURL(blob);
                        } else {
                            reject(new Error('XMLHttpRequest失败: ' + xhr.status));
                        }
                    };
                    
                    xhr.onerror = function() {
                        reject(new Error('网络请求失败'));
                    };
                    
                    xhr.send();
                });
            """, blob_url)
            
            if base64_data and 'base64' in base64_data:
                # 确定文件扩展名
                mime_type = base64_data.get('mimeType', 'image/jpeg')
                extension = mime_type.split('/')[-1]
                if extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    extension = 'jpg'
                
                # 更新文件名扩展名
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    filename = f"{os.path.splitext(filename)[0]}.{extension}"
                    filepath = os.path.join(image_dir, filename)
                
                # 解码base64并保存文件
                image_data = base64.b64decode(base64_data['base64'])
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                print(f"  图片下载成功: {filename} ({len(image_data)} bytes)")
                return filepath
            else:
                print(f"  获取base64数据失败")
                return None
                
        except Exception as e:
            print(f"  下载Blob图片失败: {e}")
            return None
    
    def download_regular_image(self, url, filename):
        """使用JavaScript下载常规HTTP图片"""
        try:
            # 创建图片保存目录
            image_dir = 'feishu_wiki_manual/images'
            os.makedirs(image_dir, exist_ok=True)
            
            # 生成完整的文件路径
            filepath = os.path.join(image_dir, filename)
            
            # 如果图片已经存在，跳过下载
            if os.path.exists(filepath):
                print(f"  图片已存在: {filename}")
                return filepath
            
            print(f"  下载常规图片: {filename}")
            
            # 使用JavaScript通过fetch API获取图片
            base64_data = self.driver.execute_script("""
                // 通过fetch API获取图片并转换为base64
                return new Promise((resolve, reject) => {
                    fetch(arguments[0], {
                        mode: 'cors',
                        credentials: 'include'
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('HTTP错误: ' + response.status);
                        }
                        return response.blob();
                    })
                    .then(blob => {
                        const reader = new FileReader();
                        reader.onloadend = function() {
                            const base64data = reader.result;
                            const base64 = base64data.split(',')[1];
                            resolve({
                                base64: base64,
                                mimeType: blob.type,
                                size: blob.size
                            });
                        };
                        reader.onerror = function() {
                            reject(new Error('FileReader读取失败'));
                        };
                        reader.readAsDataURL(blob);
                    })
                    .catch(error => {
                        reject(error);
                    });
                });
            """, url)
            
            if base64_data and 'base64' in base64_data:
                # 确定文件扩展名
                mime_type = base64_data.get('mimeType', 'image/jpeg')
                extension = mime_type.split('/')[-1]
                if extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    extension = 'jpg'
                
                # 更新文件名扩展名
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    filename = f"{os.path.splitext(filename)[0]}.{extension}"
                    filepath = os.path.join(image_dir, filename)
                
                # 解码base64并保存文件
                image_data = base64.b64decode(base64_data['base64'])
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                print(f"  图片下载成功: {filename} ({len(image_data)} bytes)")
                return filepath
            else:
                print(f"  获取base64数据失败")
                return None
                
        except Exception as e:
            print(f"  下载常规图片失败: {e}")
            return None
    
    def save_images_from_session(self, images_data, session_id, scroll_position):
        """从当前会话中保存图片"""
        new_images = []
        
        for img_data in images_data:
            # 检查是否已存在相同的图片（根据src去重）
            is_duplicate = False
            for existing in self.all_images:
                if existing['src'] == img_data['src']:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # 生成图片文件名
                src = img_data['src']
                alt = img_data['alt'] or 'image'
                
                # 生成唯一文件名
                self.image_counter += 1
                timestamp = int(time.time())
                
                # 清理alt文本用于文件名
                clean_alt = re.sub(r'[\\/*?:"<>|]', '_', alt)
                clean_alt = re.sub(r'\s+', '_', clean_alt)
                clean_alt = clean_alt[:50]  # 限制长度
                
                if not clean_alt or clean_alt == '图片':
                    clean_alt = f"image_{self.image_counter}"
                
                # 添加会话信息
                img_data['scroll_session'] = session_id
                img_data['scroll_position'] = scroll_position
                
                # 根据URL类型选择下载方法
                if src.startswith('blob:'):
                    filename = f"{clean_alt}_{timestamp}.jpg"
                    img_data['saved_filename'] = filename
                    
                    # 下载Blob图片
                    local_path = self.download_blob_image(src, filename)
                    if local_path:
                        img_data['local_path'] = local_path
                        img_data['download_success'] = True
                    else:
                        img_data['local_path'] = None
                        img_data['download_success'] = False
                    
                else:
                    # 处理常规URL
                    filename = src.split('/')[-1].split('?')[0]
                    if not filename or len(filename) < 5:
                        filename = f"{clean_alt}_{timestamp}.jpg"
                    
                    # 清理文件名
                    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
                    filename = re.sub(r'\s+', '_', filename)
                    
                    # 确保文件扩展名
                    if '.' not in filename[-5:]:
                        filename += '.jpg'
                    
                    img_data['saved_filename'] = filename
                    
                    # 下载常规图片
                    local_path = self.download_regular_image(src, filename)
                    if local_path:
                        img_data['local_path'] = local_path
                        img_data['download_success'] = True
                    else:
                        img_data['local_path'] = None
                        img_data['download_success'] = False
                
                new_images.append(img_data)
        
        return new_images
    
    def manual_scroll_collect(self):
        """手动滚动收集模式"""
        print("\n" + "="*60)
        print("手动滚动收集模式")
        print("="*60)
        print("操作说明:")
        print("1. 按 PageDown 键滚动页面")
        print("2. 按 Enter 键收集当前可视区域内容")
        print("3. 按 ESC 键结束收集")
        print("4. 按 's' 键显示当前收集统计")
        print("5. 按 'p' 键打印最后收集的5行内容")
        print("6. 按 'i' 键显示图片统计")
        print("7. 按 't' 键测试图片下载")
        print("="*60 + "\n")
        
        scroll_session = 0
        
        while True:
            print(f"\n当前滚动会话: {scroll_session + 1}")
            print("等待用户操作...")
            
            # 等待用户输入
            user_input = input("操作 (PageDown后按Enter收集，ESC结束，s统计，p预览，i图片，t测试): ").strip().lower()
            
            if user_input == '':
                # 按Enter键收集当前内容
                print(f"\n收集会话 {scroll_session + 1} 的内容...")
                
                # 获取当前滚动位置
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                
                # 提取当前内容
                content_data = self.extract_current_view_content()
                
                if content_data:
                    # 记录会话信息
                    session_info = {
                        'session_id': scroll_session,
                        'scroll_position': current_scroll,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'total_lines': content_data['totalLines'],
                        'visible_lines': content_data['visibleLines'],
                        'total_images': content_data.get('totalImages', 0),
                        'visible_images': content_data.get('visibleImages', 0)
                    }
                    
                    # 只添加新内容（根据元素索引去重）
                    new_lines = []
                    for line in content_data.get('lines', []):
                        # 检查是否已存在相同的文本（简单去重）
                        is_duplicate = False
                        for existing in self.all_content:
                            if (existing.get('text') == line.get('text') and 
                                existing.get('blockType') == line.get('blockType')):
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            new_lines.append(line)
                    
                    # 保存新图片
                    new_images = []
                    if 'images' in content_data and content_data['images']:
                        new_images = self.save_images_from_session(
                            content_data['images'], 
                            scroll_session, 
                            current_scroll
                        )
                    
                    if new_lines or new_images:
                        print(f"  收集到 {len(new_lines)} 个新内容块")
                        print(f"  收集到 {len(new_images)} 个新图片")
                        
                        # 统计Blob图片数量
                        blob_count = sum(1 for img in new_images if img.get('isBlobUrl', False))
                        if blob_count > 0:
                            print(f"    其中 {blob_count} 个是Blob URL图片")
                        
                        # 添加会话信息到每行
                        for line in new_lines:
                            line['scroll_session'] = scroll_session
                            line['scroll_position'] = current_scroll
                        
                        self.all_content.extend(new_lines)
                        self.all_images.extend(new_images)
                        
                        # 记录会话
                        session_info['new_lines'] = len(new_lines)
                        session_info['new_images'] = len(new_images)
                        self.scroll_sessions.append(session_info)
                        
                        # 显示收集的内容预览
                        if new_lines:
                            print("  文本内容预览:")
                            for i, line in enumerate(new_lines[:2]):  # 只显示前2行
                                prefix = ""
                                if line['blockType'].startswith('h'):
                                    prefix = f"[{line['blockType']}] "
                                elif line['isList']:
                                    prefix = f"[列表-{line['listType']}] "
                                elif line['isCode']:
                                    prefix = "[代码] "
                                else:
                                    prefix = "[段落] "
                                
                                text_preview = line['text'][:50] + ("..." if len(line['text']) > 50 else "")
                                print(f"    {i+1}. {prefix}{text_preview}")
                            
                            if len(new_lines) > 2:
                                print(f"    ... 还有 {len(new_lines) - 2} 行未显示")
                        
                        # 显示收集的图片预览
                        if new_images:
                            print("  图片预览:")
                            for i, img in enumerate(new_images[:3]):  # 只显示前3张
                                alt_preview = img['alt'][:30] + ("..." if len(img['alt']) > 30 else "")
                                url_type = "Blob" if img.get('isBlobUrl', False) else "HTTP"
                                print(f"    {i+1}. [{url_type}图片] {alt_preview}")
                                print(f"       尺寸: {img.get('displayWidth', 0)}x{img.get('displayHeight', 0)}")
                                if 'saved_filename' in img:
                                    status = "✓" if img.get('download_success') else "✗"
                                    print(f"       保存: {status} {img['saved_filename']}")
                            
                            if len(new_images) > 3:
                                print(f"    ... 还有 {len(new_images) - 3} 张图片未显示")
                    
                    else:
                        print("  没有发现新内容")
                    
                    scroll_session += 1
                
                else:
                    print("  未提取到内容")
            
            elif user_input == 'esc' or user_input == 'exit':
                print("\n结束收集模式")
                break
            
            elif user_input == 's':
                # 显示统计信息
                self.show_statistics()
            
            elif user_input == 'p':
                # 显示最后收集的内容
                self.preview_last_content()
            
            elif user_input == 'i':
                # 显示图片统计
                self.show_image_statistics()
            
            elif user_input == 't':
                # 测试图片下载
                self.test_image_download()
            
            else:
                print("无效输入，请按Enter、ESC、s、p、i或t")
    
    def test_image_download(self):
        """测试图片下载功能"""
        print("\n测试图片下载功能...")
        
        # 获取当前可见的图片
        test_result = self.driver.execute_script("""
            // 获取当前可见的图片
            const images = Array.from(document.querySelectorAll('img[src^="blob:"]')).slice(0, 1);
            
            if (images.length === 0) {
                return { success: false, message: "未找到Blob图片" };
            }
            
            const img = images[0];
            return {
                success: true,
                src: img.src,
                alt: img.alt || "测试图片",
                width: img.width,
                height: img.height
            };
        """)
        
        if test_result.get('success'):
            print(f"  找到测试图片: {test_result.get('alt')}")
            print(f"  Blob URL: {test_result.get('src')[:80]}...")
            
            # 尝试下载测试图片
            filename = f"test_image_{int(time.time())}.jpg"
            print(f"  尝试下载为: {filename}")
            
            local_path = self.download_blob_image(test_result['src'], filename)
            if local_path:
                print(f"  ✓ 测试图片下载成功: {local_path}")
                
                # 显示文件信息
                if os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    print(f"    文件大小: {file_size} bytes")
            else:
                print(f"  ✗ 测试图片下载失败")
        else:
            print(f"  {test_result.get('message', '测试失败')}")
    
    def show_statistics(self):
        """显示收集统计信息"""
        print("\n" + "="*60)
        print("收集统计")
        print("="*60)
        
        if not self.all_content and not self.all_images:
            print("尚未收集到任何内容")
            return
        
        # 按类型统计文本内容
        type_stats = {}
        for item in self.all_content:
            item_type = item['blockType']
            type_stats[item_type] = type_stats.get(item_type, 0) + 1
        
        print(f"总收集行数: {len(self.all_content)}")
        print(f"总收集图片数: {len(self.all_images)}")
        print(f"滚动会话数: {len(self.scroll_sessions)}")
        
        if self.all_content:
            print("\n内容类型分布:")
            for item_type, count in sorted(type_stats.items()):
                print(f"  {item_type}: {count} 行")
        
        # 图片统计
        if self.all_images:
            downloaded = sum(1 for img in self.all_images if img.get('download_success', False))
            blob_images = sum(1 for img in self.all_images if img.get('isBlobUrl', False))
            
            print(f"\n图片统计:")
            print(f"  总图片数: {len(self.all_images)}")
            print(f"  Blob URL图片: {blob_images}")
            print(f"  HTTP URL图片: {len(self.all_images) - blob_images}")
            print(f"  成功下载: {downloaded} 张")
            print(f"  下载失败: {len(self.all_images) - downloaded} 张")
        
        # 显示会话信息
        if self.scroll_sessions:
            print("\n滚动会话详情:")
            for i, session in enumerate(self.scroll_sessions):
                session_info = f"会话 {i+1}: 位置={session['scroll_position']}px"
                if 'new_lines' in session:
                    session_info += f", 新行数={session['new_lines']}"
                if 'new_images' in session:
                    session_info += f", 新图片数={session['new_images']}"
                session_info += f", 时间={session['timestamp']}"
                print(f"  {session_info}")
        
        print("="*60)
    
    def show_image_statistics(self):
        """显示图片详细统计信息"""
        print("\n" + "="*60)
        print("图片统计详情")
        print("="*60)
        
        if not self.all_images:
            print("尚未收集到任何图片")
            return
        
        print(f"总图片数: {len(self.all_images)}")
        
        # 按类型统计
        blob_count = sum(1 for img in self.all_images if img.get('isBlobUrl', False))
        downloaded_count = sum(1 for img in self.all_images if img.get('download_success', False))
        
        print(f"\n图片类型:")
        print(f"  Blob URL图片: {blob_count}")
        print(f"  常规URL图片: {len(self.all_images) - blob_count}")
        print(f"  下载成功: {downloaded_count}")
        print(f"  下载失败: {len(self.all_images) - downloaded_count}")
        
        # 显示图片详细信息
        print(f"\n图片详细信息 (显示前5张):")
        for i, img in enumerate(self.all_images[:5]):
            alt_preview = img['alt'][:40] + ("..." if len(img['alt']) > 40 else "")
            
            print(f"\n  {i+1}. {alt_preview}")
            print(f"     类型: {'Blob URL' if img.get('isBlobUrl', False) else 'HTTP URL'}")
            print(f"     会话: {img.get('scroll_session', 'N/A') + 1 if img.get('scroll_session') != -1 else 'N/A'}")
            print(f"     位置: {img.get('scroll_position', 'N/A')}px")
            print(f"     尺寸: {img.get('displayWidth', 0)}x{img.get('displayHeight', 0)}")
            
            if 'saved_filename' in img:
                status = "✓ 已下载" if img.get('download_success') else "✗ 下载失败"
                print(f"     保存: {img['saved_filename']} ({status})")
            
            # 显示部分URL
            src_preview = img['src'][:60] + ("..." if len(img['src']) > 60 else "")
            print(f"     链接: {src_preview}")
        
        if len(self.all_images) > 5:
            print(f"\n... 还有 {len(self.all_images) - 5} 张图片未显示")
        
        print("="*60)
    
    def preview_last_content(self, count=5):
        """预览最后收集的内容"""
        print(f"\n最后 {count} 个收集的内容:")
        print("-"*60)
        
        if not self.all_content and not self.all_images:
            print("无内容")
            return
        
        # 合并内容和图片按时间排序（假设按添加顺序）
        all_items = []
        all_items.extend([(item.get('scroll_session', -1), item) for item in self.all_content])
        all_items.extend([(item.get('scroll_session', -1), item) for item in self.all_images])
        
        # 按会话和索引排序
        all_items.sort(key=lambda x: (x[0], x[1].get('index', 0)))
        
        start_idx = max(0, len(all_items) - count)
        for i in range(start_idx, len(all_items)):
            session, item = all_items[i]
            item_type = item.get('elementType', 'unknown')
            
            if item_type == 'text':
                prefix = ""
                if item['blockType'].startswith('h'):
                    prefix = f"[{item['blockType']}] "
                elif item['isList']:
                    prefix = f"[列表-{item['listType']}] "
                elif item['isCode']:
                    prefix = "[代码] "
                else:
                    prefix = "[段落] "
                
                session_info = f"(会话{item.get('scroll_session', -1) + 1 if item.get('scroll_session') != -1 else 'N/A'}, 位置{item.get('scroll_position', 'N/A')}px)"
                
                print(f"{i+1}. {prefix}{item['text'][:80]}{'...' if len(item['text']) > 80 else ''}")
                print(f"   {session_info}")
            
            elif item_type == 'image':
                alt_preview = item['alt'][:50] + ("..." if len(item['alt']) > 50 else "")
                session_info = f"(会话{item.get('scroll_session', -1) + 1 if item.get('scroll_session') != -1 else 'N/A'}, 位置{item.get('scroll_position', 'N/A')}px)"
                
                url_type = "Blob" if item.get('isBlobUrl', False) else "HTTP"
                print(f"{i+1}. [{url_type}图片] {alt_preview}")
                print(f"   尺寸: {item.get('displayWidth', 0)}x{item.get('displayHeight', 0)} {session_info}")
                if 'saved_filename' in item:
                    status = "✓" if item.get('download_success') else "✗"
                    print(f"   保存: {status} {item['saved_filename']}")
            
            print()
    
    def generate_markdown(self):
        """生成Markdown格式的内容（包含图片引用）"""
        print("\n生成Markdown格式...")
        
        if not self.all_content and not self.all_images:
            print("没有内容可生成")
            return ""
        
        markdown_lines = []
        image_counter = 0
        
        # 合并所有内容（文本和图片），按收集顺序排序
        all_content_sorted = sorted(
            self.all_content + self.all_images,
            key=lambda x: (x.get('scroll_session', 0), x.get('index', 0))
        )
        
        for item in all_content_sorted:
            if item.get('elementType') == 'text':
                text = item['text']
                
                # 根据类型格式化
                if item['blockType'].startswith('h'):
                    # 标题
                    level = int(item['blockType'][1]) if len(item['blockType']) > 1 else 1
                    markdown_lines.append(f"\n{'#' * level} {text}\n")
                
                elif item['isList']:
                    # 列表
                    indent = "  " * (item['listLevel'] or 0)
                    if item['listType'] == 'ordered':
                        markdown_lines.append(f"{indent}1. {text}")
                    else:
                        markdown_lines.append(f"{indent}- {text}")
                
                elif item['isCode']:
                    # 代码
                    markdown_lines.append(f"`{text}`")
                
                else:
                    # 普通段落
                    markdown_lines.append(text)
            
            elif item.get('elementType') == 'image':
                # 图片
                image_counter += 1
                
                alt_text = item.get('alt', f'图片 {image_counter}')
                description = item.get('description', '')
                
                # 构建图片引用
                if 'local_path' in item and item.get('download_success'):
                    # 使用相对路径引用本地图片
                    local_path = item['local_path']
                    if os.path.exists(local_path):
                        # 使用相对于Markdown文件的路径
                        rel_path = os.path.relpath(local_path, 'feishu_wiki_manual')
                        img_markdown = f"\n![{alt_text}]({rel_path})"
                    else:
                        # 使用原始URL
                        img_markdown = f"\n![{alt_text}]({item['src']})"
                else:
                    # 使用原始URL
                    img_markdown = f"\n![{alt_text}]({item['src']})"
                
                if description:
                    img_markdown += f"\n*{description}*"
                
                markdown_lines.append(img_markdown)
        
        return "\n".join(markdown_lines)
    
    def get_metadata(self):
        """获取元数据"""
        try:
            title = self.driver.execute_script("""
                // 获取标题
                const titleSelectors = [
                    '.note-title__input-text',
                    '.wiki-suite-title',
                    'h1:first-of-type',
                    '.page-block-content',
                    '[data-string="true"]'
                ];
                
                for (const selector of titleSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const text = element.textContent || element.innerText || element.value || '';
                        const trimmed = text.trim();
                        if (trimmed && trimmed.length > 5 && trimmed.length < 100) {
                            return trimmed;
                        }
                    }
                }
                
                return document.title.replace('飞书 - ', '').replace(' - 飞书', '');
            """)
            
            # 获取作者
            author = self.driver.execute_script("""
                const authorSelectors = [
                    '.docs-info-avatar-name-text',
                    '.author-info',
                    '.user-name'
                ];
                
                for (const selector of authorSelectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const element of elements) {
                        const text = element.textContent || '';
                        if (text.trim() && text.length < 20) {
                            return text.trim();
                        }
                    }
                }
                return '';
            """)
            
            # 获取修改时间
            update_time = self.driver.execute_script("""
                const timeSelectors = [
                    '.note-title__time',
                    '[data-testid="metaTime"]',
                    '.doc-info-time-item'
                ];
                
                for (const selector of timeSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const text = element.textContent || '';
                        if (text.trim()) {
                            return text.trim();
                        }
                    }
                }
                return '';
            """)
            
            return {
                'title': title,
                'author': author,
                'update_time': update_time,
                'url': self.driver.current_url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'collection_mode': 'manual',
                'scroll_sessions': len(self.scroll_sessions),
                'total_lines': len(self.all_content),
                'total_images': len(self.all_images)
            }
            
        except Exception as e:
            logger.error(f"获取元数据失败: {e}")
            return {
                'title': '未知标题',
                'author': '',
                'update_time': '',
                'url': self.target_url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'collection_mode': 'manual'
            }
    
    def save_results(self):
        """保存收集结果"""
        try:
            # 获取元数据
            metadata = self.get_metadata()
            
            # 生成Markdown
            markdown_content = self.generate_markdown()
            
            # 创建输出目录
            output_dir = 'feishu_wiki_manual'
            os.makedirs(output_dir, exist_ok=True)
            
            # 创建安全的文件名
            title = metadata['title']
            title = re.sub(r'[\\/*?:"<>|]', '_', title)
            title = re.sub(r'\s+', ' ', title).strip()
            title = title[:100]
            
            timestamp = int(time.time())
            filename = f"{title}_manual_{timestamp}"
            
            # 保存Markdown文件
            md_filepath = os.path.join(output_dir, f"{filename}.md")
            
            full_markdown = f"""# {metadata['title']}

> **文档信息**
> - 来源: 飞书Wiki
> - 链接: {metadata['url']}
> - 作者: {metadata['author'] or '未知'}
> - 修改时间: {metadata['update_time']}
> - 爬取时间: {metadata['scraped_at']}
> - 爬取模式: {metadata['collection_mode']}
> - 滚动会话数: {metadata['scroll_sessions']}
> - 收集行数: {metadata['total_lines']}
> - 收集图片数: {metadata['total_images']}

---

{markdown_content}

---

*本文档由飞书Wiki手动爬取工具生成，采用手动滚动收集模式。*
*收集会话详情: {json.dumps(self.scroll_sessions, ensure_ascii=False, indent=2)}*
"""
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(full_markdown)
            
            # 保存详细数据
            json_filepath = os.path.join(output_dir, f"{filename}_detailed.json")
            detailed_data = {
                'metadata': metadata,
                'scroll_sessions': self.scroll_sessions,
                'content': self.all_content,
                'images': self.all_images,
                'summary': {
                    'total_content_items': len(self.all_content),
                    'total_images': len(self.all_images),
                    'downloaded_images': sum(1 for img in self.all_images if img.get('download_success', False)),
                    'blob_images': sum(1 for img in self.all_images if img.get('isBlobUrl', False)),
                    'unique_texts': len(set(item.get('text', '') for item in self.all_content)),
                    'content_types': {},
                    'image_stats': {}
                }
            }
            
            # 统计内容类型
            type_stats = {}
            for item in self.all_content:
                item_type = item.get('blockType', 'unknown')
                type_stats[item_type] = type_stats.get(item_type, 0) + 1
            detailed_data['summary']['content_types'] = type_stats
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 文件保存成功:")
            print(f"  Markdown文件: {os.path.abspath(md_filepath)}")
            print(f"  详细数据文件: {os.path.abspath(json_filepath)}")
            print(f"  收集行数: {len(self.all_content)}")
            print(f"  收集图片数: {len(self.all_images)}")
            print(f"  滚动会话: {len(self.scroll_sessions)}")
            
            # 显示图片下载总结
            if self.all_images:
                downloaded = sum(1 for img in self.all_images if img.get('download_success', False))
                blob_count = sum(1 for img in self.all_images if img.get('isBlobUrl', False))
                print(f"  图片下载: {downloaded}/{len(self.all_images)} 成功 (其中 {blob_count} 个Blob图片)")
            
            return md_filepath
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return None
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                print("\n浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("飞书Wiki手动爬取工具")
    print("手动控制滚动，分页收集内容和图片（支持Blob URL）")
    print("="*60)
    
    scraper = FeishuWikiManualScraper()
    
    try:
        # 初始化浏览器
        print("\n正在启动浏览器...")
        if not scraper.init_driver():
            print("浏览器启动失败")
            return
        
        # 访问页面并等待登录
        print("\n等待登录...")
        if not scraper.access_and_login():
            print("登录失败")
            return
        
        print("✓ 登录成功")
        
        # 开始手动收集
        print("\n开始手动滚动收集...")
        scraper.manual_scroll_collect()
        
        # 显示最终统计
        print("\n" + "="*60)
        print("收集完成")
        print("="*60)
        scraper.show_statistics()
        
        # 询问是否保存
        save_choice = input("\n是否保存收集结果？(y/n): ").strip().lower()
        if save_choice in ['y', 'yes', '是']:
            saved_file = scraper.save_results()
            if saved_file:
                print(f"\n✓ 结果已保存到: {saved_file}")
            else:
                print("\n⚠ 保存失败")
        
        print("\n程序执行完成")
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断程序")
        
        # 询问是否保存已收集的内容
        if scraper.all_content or scraper.all_images:
            save_choice = input("\n是否保存已收集的内容？(y/n): ").strip().lower()
            if save_choice in ['y', 'yes', '是']:
                scraper.save_results()
        
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按Enter键关闭浏览器...")
        scraper.close()

if __name__ == "__main__":
    main()