from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests
import json
import time
import random
import os
import urllib.parse
import re
from typing import List, Dict, Any

print("🚀 启动批量Selenium爬虫（自动获取地区列表并生成坐标文件）...")

class GeocoderAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_coordinates(self, search_query: str) -> Dict:
        """
        使用Photon API获取坐标
        """
        url = "https://photon.komoot.io/api/"
        params = {
            'q': search_query,
            'limit': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                coordinates = feature['geometry']['coordinates']
                # Photon返回的是[lon, lat]格式
                return {
                    "lat": round(float(coordinates[1]), 6),
                    "lng": round(float(coordinates[0]), 6)
                }
        except Exception as e:
            print(f"Photon API查询失败 {search_query}: {e}")
        
        return None

def extract_city_name_from_url(url: str) -> str:
    """
    从URL中提取城市名称
    例如: "/industries/north-america/american-game-industry/california/san-francisco" -> "San Francisco"
    """
    match = re.search(r'/([^/]+)$', url)
    if match:
        slug = match.group(1)
        city_name = ' '.join(word.capitalize() for word in slug.split('-'))
        return city_name
    return ""

def get_location_from_filename(filename: str) -> str:
    """
    从文件名提取位置信息
    例如: "california_cities.json" -> "California, USA"
    """
    # 移除文件扩展名
    basename = os.path.splitext(filename)[0]
    
    # 提取主要位置名称（假设格式为"位置_cities.json"）
    location_match = re.match(r'^([^_]+)', basename)
    if location_match:
        location = location_match.group(1)
        # 将位置名称首字母大写
        location = location.capitalize()
        
        # 特殊处理：如果是美国州名，格式为"州名, USA"
        us_states = [
            'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado',
            'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho',
            'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana',
            'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota',
            'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new-hampshire',
            'new-jersey', 'new-mexico', 'new-york', 'north-carolina', 'north-dakota',
            'ohio', 'oklahoma', 'oregon', 'pennsylvania', 'rhode-island', 'south-carolina',
            'south-dakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia',
            'washingtone', 'west-virginia', 'wisconsin', 'wyoming'
        ]
        
        # 检查是否是已知的美国州
        if location.lower() in us_states:
            return f"{location}, USA"
        else:
            # 对于加拿大省份，格式为"省份, Canada"
            canada_provinces = [
                'ontario', 'quebec', 'british-columbia', 'alberta', 'manitoba',
                'saskatchewan', 'nova-scotia', 'new-brunswick', 'newfoundland-and-labrador',
                'prince-edward-island'
            ]
            if location.lower() in canada_provinces:
                return f"{location}, Canada"
            else:
                # 对于其他国家或城市，直接返回位置名称
                return f"{location}, Singapore"
    
    # 如果无法从文件名确定位置，使用默认值
    return "Canada"

def load_cities_from_json(file_path: str) -> tuple[List[Dict[str, Any]], str]:
    """
    从JSON文件加载城市数据，并返回数据和位置信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 从文件名获取位置信息
        filename = os.path.basename(file_path)
        location = get_location_from_filename(filename)
        
        cities = []
        for item in data:
            city_name = item.get('name', '')
            city_slug = item.get('slug', '')
            if not city_name:
                city_name = extract_city_name_from_url(item.get('url', ''))
            
            if city_name:
                cities.append({
                    'original_name': city_name,
                    'slug': city_slug,  # 确保包含slug
                    'search_name': f"{city_name}, {location}",
                    'location': location,
                    'url': item.get('url', ''),
                    'companies_count': item.get('companies_count', ''),
                    'events_count': item.get('events_count', ''),
                    'jobs_count': item.get('jobs_count', '')
                })
        
        return cities, location
    except Exception as e:
        print(f"加载城市数据失败: {e}")
        return [], ""

def batch_geocode_cities(cities_data: List[Dict]) -> Dict[str, Dict]:
    """
    批量查询城市坐标 - 修复：使用slug作为键
    """
    geocoder = GeocoderAPI()
    results = {}
    
    for i, city_info in enumerate(cities_data):
        city_name = city_info['original_name']
        city_slug = city_info['slug']  # 使用slug作为标识符
        search_name = city_info['search_name']
        
        print(f"查询中 ({i+1}/{len(cities_data)}): {search_name} (slug: {city_slug})")
        
        coordinates = geocoder.get_coordinates(search_name)
        if coordinates:
            # 修复：使用slug作为键，而不是城市名称
            results[city_slug] = coordinates
            print(f"  ✓ 成功: {coordinates}")
        else:
            print(f"  ✗ 失败: {search_name}")
        
        # 添加延迟避免频繁请求
        if i < len(cities_data) - 1:
            time.sleep(1)
    
    return results

def save_coordinates_to_json(data: Dict, location: str, filename: str = None):
    """
    保存为指定格式的JSON文件，根据位置信息命名，并保存到coordinates文件夹
    """
    # 创建coordinates文件夹
    coordinates_dir = "coordinates"
    os.makedirs(coordinates_dir, exist_ok=True)
    
    if not filename:
        # 根据位置信息生成文件名
        safe_location = location.split(',')[0].lower().replace(' ', '_')
        filename = f"{safe_location}_cities_coordinates.json"
    
    # 完整的文件路径
    file_path = os.path.join(coordinates_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
    
    print(f"\n坐标数据已保存到: {file_path}")
    return file_path

def generate_coordinates_file(cities_json_file: str):
    """
    根据城市JSON文件生成坐标文件
    """
    print(f"\n{'='*60}")
    print("🗺️  开始生成城市坐标文件")
    print(f"{'='*60}")
    
    cities_data, location = load_cities_from_json(cities_json_file)
    
    if not cities_data:
        print(f"无法从 {cities_json_file} 加载城市数据")
        return None
    
    print(f"从 {cities_json_file} 加载了 {len(cities_data)} 个城市")
    print(f"检测到的位置: {location}")
    print("开始批量查询城市经纬度...")
    print("-" * 50)
    
    # 批量查询
    results = batch_geocode_cities(cities_data)
    
    # 显示统计信息
    print("\n" + "=" * 50)
    print(f"查询完成: 成功 {len(results)}/{len(cities_data)} 个城市")
    
    # 保存结果到coordinates文件夹
    coordinates_file = save_coordinates_to_json(results, location)
    
    # 显示部分结果预览
    print("\n结果预览:")
    print("-" * 30)
    for slug, coords in list(results.items())[:5]:
        print(f'"{slug}": {{ "lat": {coords["lat"]}, "lng": {coords["lng"]} }}')
    
    return coordinates_file

def setup_driver():
    """设置Chrome驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def get_region_name_from_url(url):
    """从URL中提取地区名称（最后一个斜杠后的单词）"""
    try:
        # 移除末尾的斜杠并分割URL
        cleaned_url = url.rstrip('/')
        region_name = cleaned_url.split('/')[-1]
        return region_name
    except Exception as e:
        print(f"❌ 从URL提取地区名称失败: {e}")
        return "unknown_region"

def extract_regions_from_country_page(driver, country_url):
    """从国家页面提取所有地区列表"""
    try:
        print(f"🌐 访问国家页面获取地区列表: {country_url}")
        
        driver.get(country_url)
        
        # 等待页面加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ 国家页面加载完成")
        time.sleep(3)
        
        # 提取页面内容
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        regions = []
        
        # 查找所有地区卡片 - 根据提供的HTML结构
        region_cards = soup.find_all('a', class_=lambda x: x and 'IndustryCard-root' in str(x) if x else False)
        
        print(f"🔍 找到 {len(region_cards)} 个地区卡片")
        
        for card in region_cards:
            try:
                # 提取地区名称
                region_name_elem = card.find('span', class_=lambda x: x and 'IndustryCard-cardTitle' in str(x) if x else False)
                if region_name_elem:
                    region_name = region_name_elem.get_text(strip=True)
                    
                    # 提取地区URL
                    region_url = card.get('href', '')
                    if region_url:
                        # 构建完整URL
                        if not region_url.startswith('http'):
                            region_url = "https://gamecompanies.com" + region_url
                        
                        # 从URL提取slug
                        region_slug = region_url.split('/')[-1]
                        
                        region_data = {
                            'name': region_name,
                            'slug': region_slug,  # 添加slug字段
                            'url': region_url
                        }
                        
                        # 提取统计信息
                        chips = card.find_all('span', class_=lambda x: x and 'MuiChip-label' in str(x) if x else False)
                        for chip in chips:
                            chip_text = chip.get_text(strip=True)
                            if 'companies' in chip_text.lower():
                                region_data['companies_count'] = chip_text
                            elif 'jobs' in chip_text.lower():
                                region_data['jobs_count'] = chip_text
                            elif 'events' in chip_text.lower():
                                region_data['events_count'] = chip_text
                        
                        regions.append(region_data)
                        print(f"  ✅ 提取地区: {region_name} (slug: {region_slug}) - {region_url}")
                        
            except Exception as e:
                print(f"  ❌ 处理地区卡片时出错: {e}")
                continue
        
        # 保存地区列表
        regions_filename = "turkish_regions.json"
        with open(regions_filename, 'w', encoding='utf-8') as f:
            json.dump(regions, f, indent=2, ensure_ascii=False)
        print(f"💾 地区列表已保存到 {regions_filename}，共 {len(regions)} 个地区")
        
        return regions, regions_filename
        
    except Exception as e:
        print(f"❌ 获取地区列表失败: {e}")
        return [], None

def extract_cities_from_region_page(driver, region_url):
    """从地区页面提取所有城市列表"""
    try:
        # 从URL获取地区名称
        region_name = get_region_name_from_url(region_url)
        print(f"🌐 访问{region_name}页面获取城市列表...")
        
        driver.get(region_url)
        
        # 等待页面加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print(f"✅ {region_name}页面加载完成")
        time.sleep(3)
        
        # 点击Load More按钮直到加载所有城市
        print("🔄 加载所有城市...")
        cities_loaded = click_cities_load_more(driver)
        
        # 提取城市信息
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        cities = []
        
        # 查找所有城市卡片
        city_cards = soup.find_all('a', class_=lambda x: x and 'IndustryCard-root' in x)
        print(f"🔍 找到 {len(city_cards)} 个城市卡片")
        
        for card in city_cards:
            try:
                # 提取城市名称
                city_name_elem = card.find('span', class_=lambda x: x and 'IndustryCard-cardTitle' in x)
                if city_name_elem:
                    city_name = city_name_elem.get_text(strip=True)
                    
                    # 提取城市URL
                    city_url = card.get('href', '')
                    if city_url:
                        # 从URL中提取城市slug（最后一个部分）
                        city_slug = city_url.split('/')[-1]
                        
                        city_data = {
                            'name': city_name,
                            'slug': city_slug,  # 这里已经是英文slug
                            'url': city_url
                        }
                        
                        # 提取公司数量信息
                        chips = card.find_all('span', class_=lambda x: x and 'MuiChip-label' in x)
                        for chip in chips:
                            chip_text = chip.get_text(strip=True)
                            if 'companies' in chip_text.lower():
                                city_data['companies_count'] = chip_text
                            elif 'jobs' in chip_text.lower():
                                city_data['jobs_count'] = chip_text
                            elif 'events' in chip_text.lower():
                                city_data['events_count'] = chip_text
                        
                        cities.append(city_data)
                        print(f"  ✅ 提取城市: {city_name} (slug: {city_slug})")
                        
            except Exception as e:
                print(f"  ❌ 处理城市卡片时出错: {e}")
                continue
        
        # 修复：使用地区的slug作为文件名（从URL提取）
        region_slug = region_url.split('/')[-1]
        cities_filename = f"{region_slug}_cities.json"
        
        with open(cities_filename, 'w', encoding='utf-8') as f:
            json.dump(cities, f, indent=2, ensure_ascii=False)
        print(f"💾 城市列表已保存到 {cities_filename}，共 {len(cities)} 个城市")
        
        return cities, region_name, cities_filename
        
    except Exception as e:
        print(f"❌ 获取城市列表失败: {e}")
        return [], "unknown_region", None

def click_cities_load_more(driver, max_clicks=20):
    """点击城市页面的Load More按钮"""
    click_count = 0
    
    while click_count < max_clicks:
        try:
            # 等待页面稳定
            time.sleep(2)
            
            # 查找Load More按钮
            load_more_button = None
            load_more_selectors = [
                "button:contains('Load more')",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(., 'Load more')]",
                ".GCButton-root"
            ]
            
            for selector in load_more_selectors:
                try:
                    if selector.startswith("//"):
                        load_more_button = driver.find_element(By.XPATH, selector)
                    else:
                        # 使用JavaScript查找包含"Load more"文本的按钮
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if "load more" in button.text.lower():
                                load_more_button = button
                                break
                    
                    if load_more_button:
                        break
                except:
                    continue
            
            if not load_more_button:
                print("❌ 找不到Load More按钮，可能已加载完毕")
                break
            
            # 检查按钮是否可点击
            if not load_more_button.is_enabled():
                print("❌ Load More按钮不可点击")
                break
            
            # 滚动到按钮位置
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)
            time.sleep(1)
            
            # 点击按钮
            print(f"🔄 点击第 {click_count + 1} 次Load More...")
            driver.execute_script("arguments[0].click();", load_more_button)
            click_count += 1
            
            # 等待新内容加载
            time.sleep(3)
            
            # 随机延迟
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"❌ 点击Load More时出错: {e}")
            break
    
    print(f"✅ 共点击 {click_count} 次Load More")
    return click_count

def extract_location_from_url(url):
    """从URL中提取城市和地区信息"""
    try:
        # 解析URL
        parsed_url = urllib.parse.urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        # 最后一个部分通常是城市slug
        if path_parts:
            city_slug = path_parts[-1]
            
            # 根据URL路径推断国家信息
            country = "加拿大"  # 默认值
            if 'north-america' in url and 'canadian-game-industry' in url:
                country = "加拿大"
            elif 'north-america' in url and 'american-game-industry' in url:
                country = "美国"
            elif 'turkish-game-industry' in url:
                country = "土耳其"
            elif 'new-zealand-game-industry' in url:
                country = "新西兰"
            elif 'brazilian-game-industry' in url:
                country = "巴西"
            elif 'chilean-game-industry' in url:
                country = "智利"
            elif 'swedish-game-industry' in url:
                country = "瑞典"
            elif 'german-game-industry' in url:
                country = "德国"
            elif 'polish-game-industry' in url:
                country = "波兰"
            elif 'french-game-industry' in url:
                country = "法国"
            elif 'finnish-game-industry' in url:
                country = "芬兰"
            elif 'spanish-game-industry' in url:
                country = "西班牙"
            elif 'dutch-game-industry' in url:
                country = "荷兰"
            elif 'romanian-game-industry' in url:
                country = "罗马尼亚"
            elif 'scottish-game-industry' in url:
                country = "苏格兰"
            elif 'danish-game-industry' in url:
                country = "丹麦"
            elif 'norwegian-game-industry' in url:
                country = "挪威"
            elif 'ukranian-game-industry' in url:
                country = "乌克兰"
            elif 'irish-game-industry' in url:
                country = "爱尔兰"
            elif 'czech-game-industry' in url:
                country = "捷克"
            elif 'italian-game-industry' in url:
                country = "意大利"
            elif 'austrian-game-industry' in url:
                country = "奥地利"
            elif 'belgian-game-industry' in url:
                country = "比利时"
            elif 'slovakian-game-industry' in url:
                country = "斯洛伐克"
            elif 'welsh-game-industry' in url:
                country = "威尔士"
            elif 'hungarian-game-industry' in url:
                country = "匈牙利"
            elif 'lithuanian-game-industry' in url:
                country = "立陶宛"
            elif 'maltaic-game-industry' in url:
                country = "马耳他"
            elif 'northern-irish-game-industry' in url:
                country = "北爱尔兰"
            elif 'english-game-industry' in url:
                country = "英格兰"
            elif 'serbian-game-industry' in url:
                country = "塞尔维亚"
            elif 'swiss-game-industry' in url:
                country = "瑞士"
            elif 'belarusian-game-industry' in url:
                country = "白俄罗斯"
            elif 'bulgarian-game-industry' in url:
                country = "保加利亚"
            elif 'croatian-game-industry' in url:
                country = "克罗地亚"
            elif 'estonian-game-industry' in url:
                country = "爱沙尼亚"
            elif 'icelandic-game-industry' in url:
                country = "冰岛"
            elif 'portugese-game-industry' in url:
                country = "葡萄牙"
            elif 'slovenian-game-industry' in url:
                country = "斯洛文尼亚"
            elif 'greek-game-industry' in url:
                country = "希腊"
            elif 'latvian-game-industry' in url:
                country = "拉脱维亚"
            elif 'macedonian-game-industry' in url:
                country = "北马其顿"
            elif 'moldovian-game-industry' in url:
                country = "摩尔多瓦"
            elif 'singaporean-game-industry' in url:
                country = "新加坡"
            
            return city_slug, country  # 返回slug而不是城市名称
        else:
            return "unknown", "未知国家"
            
    except Exception as e:
        print(f"❌ 从URL提取位置信息失败: {e}")
        return "unknown", "未知国家"

def click_load_more(driver, max_clicks=50):
    """点击Load More按钮直到没有更多数据"""
    click_count = 0
    total_companies = 0
    
    while click_count < max_clicks:
        try:
            # 等待页面稳定
            time.sleep(2)
            
            # 查找Load More按钮
            load_more_selectors = [
                "button[aria-label*='load more']",
                "button:contains('Load more')",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(., 'Load more')]",
                ".MuiButton-root",
                "button"
            ]
            
            load_more_button = None
            
            # 尝试不同的选择器
            for selector in load_more_selectors:
                try:
                    if selector.startswith("//"):
                        load_more_button = driver.find_element(By.XPATH, selector)
                    else:
                        load_more_button = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # 检查按钮是否包含"Load more"文本
                    if load_more_button and "load more" in load_more_button.text.lower():
                        break
                    else:
                        load_more_button = None
                except:
                    continue
            
            if not load_more_button:
                print("❌ 找不到Load More按钮")
                break
            
            # 滚动到按钮位置
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)
            time.sleep(1)
            
            # 检查按钮是否可点击
            if not load_more_button.is_enabled():
                print("❌ Load More按钮不可点击")
                break
            
            # 点击按钮
            print(f"🔄 点击第 {click_count + 1} 次Load More...")
            driver.execute_script("arguments[0].click();", load_more_button)
            click_count += 1
            
            # 等待新内容加载
            time.sleep(3)
            
            # 检查是否有新公司加载
            current_companies = count_companies(driver)
            print(f"📊 当前公司数量: {current_companies}")
            
            # 如果公司数量没有增加，可能已经加载完毕
            if current_companies <= total_companies:
                print("⚠️ 公司数量没有增加，可能已加载完毕")
                break
            
            total_companies = current_companies
            
            # 随机延迟，避免被检测
            time.sleep(random.uniform(2, 4))
            
        except TimeoutException:
            print("⏰ 等待超时，可能已加载完毕")
            break
        except NoSuchElementException:
            print("❌ 找不到Load More按钮，可能已加载完毕")
            break
        except Exception as e:
            print(f"❌ 点击Load More时出错: {e}")
            break
    
    print(f"✅ 共点击 {click_count} 次Load More")
    return click_count

def count_companies(driver):
    """计算当前页面上的公司数量"""
    try:
        company_selectors = [
            '[class*="ItemListItem-root"]',
            '[class*="company"]',
            '[class*="card"]'
        ]
        
        for selector in company_selectors:
            companies = driver.find_elements(By.CSS_SELECTOR, selector)
            if companies:
                return len(companies)
        
        return 0
    except:
        return 0

def extract_companies(driver):
    """从页面中提取公司数据"""
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    companies = []
    seen_names = set()
    
    # 查找所有公司元素
    company_elements = soup.find_all(['div', 'a'], class_=lambda x: x and any(cls in str(x) for cls in ['ItemListItem', 'company', 'card']))
    
    print(f"🔍 找到 {len(company_elements)} 个公司元素")
    
    for element in company_elements:
        try:
            company_data = {}
            
            # 提取公司名称
            name_selectors = [
                '[class*="ItemListItem-title"]',
                '[class*="title"]',
                '[class*="name"]',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
            ]
            
            name = None
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    name = name_elem.get_text(strip=True)
                    break
            
            if not name or name in seen_names:
                continue
                
            seen_names.add(name)
            company_data['name'] = name
            
            # 提取描述
            desc_selectors = [
                '[class*="ItemListItem-subtitle"]',
                '[class*="description"]',
                '[class*="body"]',
                'p'
            ]
            
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem and desc_elem.get_text(strip=True):
                    company_data['description'] = desc_elem.get_text(strip=True)
                    break
            
            # 提取图片
            img_elem = element.find('img')
            if img_elem:
                src = img_elem.get('src', '')
                if src and not src.startswith('data:'):
                    company_data['image_url'] = src
                
                # 提取srcset
                srcset = img_elem.get('srcset', '')
                if srcset:
                    company_data['image_srcset'] = srcset
            
            # 提取标签
            tags = []
            tag_elements = element.find_all(class_=lambda x: x and 'MuiChip-label' in x)
            for tag in tag_elements:
                tag_text = tag.get_text(strip=True)
                if tag_text and tag_text not in ['Studio', 'Publisher', 'Indie']:  # 过滤通用标签
                    tags.append(tag_text)
            company_data['tags'] = tags
            
            # 提取链接
            if element.name == 'a':
                company_data['link'] = element.get('href', '')
            else:
                link_elem = element.find('a')
                if link_elem:
                    company_data['link'] = link_elem.get('href', '')
            
            companies.append(company_data)
            print(f"  ✅ 提取: {name}")
            
        except Exception as e:
            print(f"  ❌ 处理元素时出错: {e}")
            continue
    
    return companies

def process_companies_data(companies_data, city_slug, country):
    """处理公司数据：删除不需要的字段，添加城市和国家信息"""
    processed_data = []
    
    for item in companies_data:
        # 创建新对象，只保留名称
        processed_item = {
            'name': item.get('name', '')
        }
        
        # 添加位置信息 - 使用slug作为城市标识
        processed_item['city'] = city_slug  # 使用slug而不是城市名称
        processed_item['country'] = country
        
        processed_data.append(processed_item)
    
    return processed_data

def save_processed_data(processed_data, city_slug, country, output_dir='processed_companies'):
    """保存处理后的数据到指定文件夹"""
    # 创建新文件夹
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建新的文件名 - 使用slug
    if processed_data:
        # 使用城市slug和国家名称创建文件名
        filename = f"{country}_{city_slug}_game_companies.json".replace(' ', '_')
    else:
        filename = "game_companies.json"
    
    # 完整的文件路径
    file_path = os.path.join(output_dir, filename)
    
    # 保存处理后的数据
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(processed_data, file, indent=2, ensure_ascii=False)
    
    print(f"💾 处理后的数据已保存为 {file_path}")
    return file_path

def scrape_single_city(city_data, base_url="https://gamecompanies.com"):
    """爬取单个城市的公司数据"""
    # 构建完整URL
    if city_data['url'].startswith('http'):
        target_url = city_data['url']
    else:
        target_url = base_url + city_data['url']
    
    # 从URL提取位置信息 - 现在返回slug
    city_slug, country = extract_location_from_url(target_url)
    print(f"📍 检测到位置信息: {city_slug}, {country}")
    
    driver = setup_driver()
    all_companies = []
    
    try:
        print(f"🌐 访问: {target_url}")
        
        driver.get(target_url)
        
        # 等待初始页面加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ 初始页面加载完成")
        time.sleep(3)
        
        # 初始公司数量
        initial_count = count_companies(driver)
        print(f"📊 初始公司数量: {initial_count}")
        
        # 点击Load More加载所有数据
        print("🔄 开始加载更多数据...")
        clicks = click_load_more(driver, max_clicks=40)  # 最多点击40次
        
        # 最终公司数量
        final_count = count_companies(driver)
        print(f"📊 最终公司数量: {final_count}")
        print(f"📈 共加载了 {final_count - initial_count} 条新数据")
        
        # 提取所有公司数据
        print("🔍 提取公司数据...")
        all_companies = extract_companies(driver)
        
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        return [], None
    finally:
        driver.quit()
        print("🔚 浏览器已关闭")
    
    # 处理数据
    if all_companies:
        print("🔄 开始处理数据...")
        processed_companies = process_companies_data(all_companies, city_slug, country)
        
        # 保存处理后的数据
        output_path = save_processed_data(processed_companies, city_slug, country)
        
        return processed_companies, output_path
    else:
        return [], None

def batch_scrape_all_cities(region_url, max_cities=None):
    """批量爬取指定地区的所有城市数据"""
    driver = setup_driver()
    
    try:
        # 第一步：获取所有城市列表
        print("=" * 60)
        print(f"🏙️  第一步：获取{get_region_name_from_url(region_url)}所有城市列表")
        print("=" * 60)
        
        cities, region_name, cities_filename = extract_cities_from_region_page(driver, region_url)
        
        if not cities:
            print("❌ 未能获取城市列表")
            return {}
        
        # 限制处理的城市数量（用于测试）
        if max_cities and max_cities < len(cities):
            cities = cities[:max_cities]
            print(f"⚠️  测试模式：只处理前 {max_cities} 个城市")
        
    finally:
        driver.quit()
    
    # 第二步：逐个爬取每个城市
    print(f"\n{'='*60}")
    print("🏢 第二步：批量爬取各城市公司数据")
    print(f"{'='*60}")
    
    results = {}
    successful_cities = 0
    
    for i, city_data in enumerate(cities, 1):
        print(f"\n🏙️  开始处理第 {i}/{len(cities)} 个城市: {city_data['name']} (slug: {city_data['slug']})")
        print(f"   城市信息: {city_data.get('companies_count', '未知')}")
        
        # 爬取单个城市
        processed_companies, output_path = scrape_single_city(city_data)
        
        # 记录结果 - 使用slug作为键
        results[city_data['slug']] = {
            'name': city_data['name'],  # 保留原始名称用于显示
            'companies_count': len(processed_companies),
            'output_path': output_path,
            'original_info': city_data.get('companies_count', '未知')
        }
        
        if len(processed_companies) > 0:
            successful_cities += 1
        
        # 添加延迟，避免请求过于频繁
        if i < len(cities):
            delay = random.uniform(8, 15)
            print(f"⏳ 等待 {delay:.1f} 秒后处理下一个城市...")
            time.sleep(delay)
    
    return results, successful_cities, len(cities), region_name, cities_filename

def batch_scrape_all_regions(country_url, max_regions=None):
    """批量爬取指定国家的所有地区数据"""
    driver = setup_driver()
    
    try:
        # 第一步：获取所有地区列表
        print("=" * 60)
        print("🏞️  第一步：获取土耳其所有地区列表")
        print("=" * 60)
        
        regions, regions_filename = extract_regions_from_country_page(driver, country_url)
        
        if not regions:
            print("❌ 未能获取地区列表")
            return {}
        
        # 限制处理的地区数量（用于测试）
        if max_regions and max_regions < len(regions):
            regions = regions[:max_regions]
            print(f"⚠️  测试模式：只处理前 {max_regions} 个地区")
        
    finally:
        driver.quit()
    
    # 第二步：逐个爬取每个地区的城市
    print(f"\n{'='*60}")
    print("🏙️  第二步：批量爬取各地区城市数据")
    print(f"{'='*60}")
    
    all_results = {}
    total_cities_processed = 0
    successful_regions = 0
    
    for i, region_data in enumerate(regions, 1):
        print(f"\n🏞️  开始处理第 {i}/{len(regions)} 个地区: {region_data['name']} (slug: {region_data['slug']})")
        print(f"   地区信息: {region_data.get('companies_count', '未知')}")
        print(f"   地区URL: {region_data['url']}")
        
        # 爬取单个地区的城市
        region_results, successful_count, total_count, region_name, cities_filename = batch_scrape_all_cities(
            region_url=region_data['url'], 
            max_cities=None  # 设置为None爬取所有城市
        )
        
        # 记录结果 - 使用slug作为键
        all_results[region_data['slug']] = {
            'name': region_data['name'],  # 保留原始名称用于显示
            'url': region_data['url'],
            'cities_count': total_count,
            'successful_cities': successful_count,
            'region_results': region_results
        }
        
        total_cities_processed += total_count
        
        if successful_count > 0:
            successful_regions += 1
        
        # 添加延迟，避免请求过于频繁
        if i < len(regions):
            delay = random.uniform(10, 20)
            print(f"⏳ 等待 {delay:.1f} 秒后处理下一个地区...")
            time.sleep(delay)
    
    return all_results, successful_regions, len(regions), total_cities_processed, regions_filename

# 运行完整流程
if __name__ == "__main__":
    print("🚀 开始自动获取地区列表并批量爬取...")
    
    # 设置要爬取的国家URL
    country_url = "https://gamecompanies.com/industries/asia/singaporean-game-industry"
    
    # 批量爬取所有地区（可以设置max_regions来限制数量进行测试）
    all_region_results, successful_region_count, total_region_count, total_cities_count, regions_filename = batch_scrape_all_regions(
        country_url=country_url, 
        max_regions=None  # 设置为None爬取所有地区
    )
    
    # 汇总统计
    print(f"\n{'='*60}")
    print("📊 批量爬取汇总结果")
    print(f"{'='*60}")
    
    total_companies_all_regions = 0
    
    for region_slug, region_result in all_region_results.items():
        region_companies = 0
        for city_slug, city_result in region_result['region_results'].items():
            region_companies += city_result['companies_count']
        
        total_companies_all_regions += region_companies
        
        status = "✅ 成功" if region_result['successful_cities'] > 0 else "❌ 失败"
        region_name = region_result['name']
        print(f"{region_name:25} : {status} - {region_result['successful_cities']:2d}/{region_result['cities_count']:2d} 个城市, {region_companies:4d} 家公司")
    
    print(f"\n🎉 批量爬取完成！")
    print(f"   国家: 土耳其")
    print(f"   成功爬取: {successful_region_count}/{total_region_count} 个地区")
    print(f"   总城市数: {total_cities_count}")
    print(f"   总公司数: {total_companies_all_regions}")
    print(f"   数据保存位置: processed_companies/ 文件夹")
    
    # 保存汇总文件
    summary_file = "turkish_scraping_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_region_results, f, indent=2, ensure_ascii=False)
    print(f"💾 汇总信息已保存为: {summary_file}")
    
    # 显示一些统计信息
    print(f"\n📈 统计信息:")
    regions_with_companies = [slug for slug, result in all_region_results.items() 
                             if any(city['companies_count'] > 0 for city in result['region_results'].values())]
    
    if regions_with_companies:
        print(f"   有公司的地区: {len(regions_with_companies)} 个")
        avg_companies_per_region = total_companies_all_regions / len(regions_with_companies) if regions_with_companies else 0
        print(f"   平均每个地区公司数: {avg_companies_per_region:.1f}")
        
        # 显示公司最多的前5个地区
        top_regions = sorted(all_region_results.items(), 
                           key=lambda x: sum(city['companies_count'] for city in x[1]['region_results'].values()), 
                           reverse=True)[:5]
        print(f"   公司最多的前5个地区:")
        for region_slug, result in top_regions:
            region_companies = sum(city['companies_count'] for city in result['region_results'].values())
            region_name = result['name']
            print(f"     {region_name}: {region_companies} 家公司")
    
    # 第三步：为所有地区生成坐标文件
    print(f"\n{'='*60}")
    print("🗺️  第三步：为所有地区生成坐标文件")
    print(f"{'='*60}")
    
    coordinates_files = []
    
    for region_slug, region_result in all_region_results.items():
        cities_filename = f"{region_slug}_cities.json"
        
        if os.path.exists(cities_filename):
            print(f"\n🌍 为 {region_result['name']} 生成坐标文件...")
            coordinates_file = generate_coordinates_file(cities_filename)
            if coordinates_file:
                coordinates_files.append(coordinates_file)
                print(f"✅ 坐标文件生成完成: {coordinates_file}")
            else:
                print(f"❌ 坐标文件生成失败: {region_result['name']}")
        else:
            print(f"⚠️  未找到城市数据文件: {cities_filename}")
            # 调试信息：列出所有可能的文件
            all_files = [f for f in os.listdir('.') if f.endswith('_cities.json')]
            print(f"   当前目录下的cities文件: {all_files}")
    
    print(f"\n🎯 坐标文件生成统计: 成功 {len(coordinates_files)} 个地区")

    # 第四步：清理临时文件
    print(f"\n{'='*60}")
    print("🧹 清理临时文件")
    print(f"{'='*60}")
    
    files_to_delete = []
    
    # 添加要删除的地区文件
    if regions_filename and os.path.exists(regions_filename):
        files_to_delete.append(regions_filename)
        print(f"🗑️  待删除地区文件: {regions_filename}")
    
    # 添加要删除的汇总文件
    if os.path.exists(summary_file):
        files_to_delete.append(summary_file)
        print(f"🗑️  待删除汇总文件: {summary_file}")
    
    # 添加要删除的城市文件 - 使用slug
    for region_slug, region_result in all_region_results.items():
        cities_filename = f"{region_slug}_cities.json"
        if os.path.exists(cities_filename):
            files_to_delete.append(cities_filename)
            print(f"🗑️  待删除城市文件: {cities_filename}")
    
    # 删除文件
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"✅ 已删除: {file_path}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ 删除失败 {file_path}: {e}")
    
    print(f"🎯 清理完成: 成功删除 {deleted_count}/{len(files_to_delete)} 个临时文件")