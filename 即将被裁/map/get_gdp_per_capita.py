import json
import wbgapi as wb
import pandas as pd
from typing import List, Dict, Any, Optional

def get_gdp_per_capita_wb(country_name: str, year: int = 2022) -> Optional[float]:
    """
    使用世界银行API获取国家人均GDP（美元）
    """
    # 国家名称到世界银行代码的映射
    country_code_mapping = {
        "中国": "CHN",
        "美国": "USA",
        "日本": "JPN",
        "德国": "DEU",
        "英国": "GBR",
        "法国": "FRA",
        "韩国": "KOR",
        "加拿大": "CAN",
        "澳大利亚": "AUS",
        "印度": "IND",
        "俄罗斯": "RUS",
        "巴西": "BRA",
        "新加坡": "SGP",
        "马来西亚": "MYS",
        "印尼": "IDN",
        "泰国": "THA",
        "越南": "VNM",
        "菲律宾": "PHL",
        "墨西哥": "MEX",
        "南非": "ZAF",
        "沙特阿拉伯": "SAU",
        "阿联酋": "ARE",
        "土耳其": "TUR",
        "意大利": "ITA",
        "西班牙": "ESP",
        "荷兰": "NLD",
        "瑞士": "CHE",
        "瑞典": "SWE",
        "挪威": "NOR",
        "丹麦": "DNK",
        "芬兰": "FIN",
        "比利时": "BEL",
        "奥地利": "AUT",
        "波兰": "POL",
        "中国台湾": "TWN",
        "中国香港": "HKG",
        "澳门": "MAC",
        "以色列": "ISR",
    "罗马尼亚": "ROU",
    "秘鲁": "PER",
    "智利": "CHL",
    "乌克兰": "UKR",
    "哥伦比亚": "COL",
    "新西兰": "NZL",
    "斯洛文尼亚": "SVN",
    "阿根廷": "ARG",
    "巴拿马": "PAN",
    "斯洛伐克": "SVK",
    "葡萄牙": "PRT",
    "巴基斯坦": "PAK",
    "保加利亚": "BGR",
    "克罗地亚": "HRV",
    "亚美尼亚": "ARM",
    "摩尔多瓦": "MDA",
    "塞浦路斯": "CYP",
    "马耳他": "MLT",
    "冰岛": "ISL",
    "爱尔兰": "IRL",
    "孟加拉": "BGD",
    "捷克": "CZE",
    "立陶宛": "LTU",
    "吉尔吉斯斯坦": "KGZ",
    "塞尔维亚": "SRB",
    "白俄罗斯": "BLR",
    "拉脱维亚": "LVA",
    "希腊": "GRC",
    "匈牙利": "HUN",
    "北马其顿": "MKD",
    }
    
    country_code = country_code_mapping.get(country_name)
    if not country_code:
        print(f"警告: 未找到国家 '{country_name}' 的代码映射")
        return None
    
    try:
        indicator = 'NY.GDP.PCAP.CD'  # GDP per capita (current US$)
        
        # 获取最近几年的数据
        start_year = year - 3
        end_year = year
        
        df = wb.data.DataFrame(
            indicator, 
            economy=country_code,
            time=range(start_year, end_year + 1),
            skipBlanks=True,
            columns='time'
        )
        
        if df.empty:
            print(f"警告: 未找到国家 '{country_name}' ({country_code}) 的GDP数据")
            return None
        
        # 获取最新年份的有效数据
        for y in range(end_year, start_year - 1, -1):
            year_str = f'YR{y}'
            if year_str in df.columns:
                value = df[year_str].iloc[0]
                if pd.notna(value):
                    return float(value)
        
        return None
        
    except Exception as e:
        print(f"获取 '{country_name}' GDP数据时出错: {e}")
        return None

def get_multiple_countries_gdp(countries: List[str], year: int = 2022) -> Dict[str, Optional[float]]:
    """
    批量获取多个国家的人均GDP
    """
    print("正在从世界银行API获取数据...")
    
    country_code_mapping = {
        "中国": "CHN", "美国": "USA", "日本": "JPN", "德国": "DEU",
         "法国": "FRA", "韩国": "KOR", "加拿大": "CAN",
        "澳大利亚": "AUS", "印度": "IND", "俄罗斯": "RUS", "巴西": "BRA",
        "新加坡": "SGP", "马来西亚": "MYS", "印尼": "IDN",
        "泰国": "THA", "越南": "VNM", "菲律宾": "PHL", "墨西哥": "MEX",
        "南非": "ZAF", "沙特阿拉伯": "SAU", "阿联酋": "ARE", "土耳其": "TUR",
        "意大利": "ITA", "西班牙": "ESP", "荷兰": "NLD", "瑞士": "CHE",
        "瑞典": "SWE", "挪威": "NOR", "丹麦": "DNK", "芬兰": "FIN",
        "比利时": "BEL", "奥地利": "AUT", "波兰": "POL", "中国台湾": "TWN",
        "中国香港": "HKG", "澳门": "MAC","以色列": "ISR",
    "罗马尼亚": "ROU",
    "秘鲁": "PER",
    "智利": "CHL",
    "乌克兰": "UKR",
    "哥伦比亚": "COL",
    "新西兰": "NZL",
    "斯洛文尼亚": "SVN",
    "阿根廷": "ARG",
    "巴拿马": "PAN",
    "斯洛伐克": "SVK",
    "葡萄牙": "PRT",
    "巴基斯坦": "PAK",
    "保加利亚": "BGR",
    "克罗地亚": "HRV",
    "亚美尼亚": "ARM",
    "摩尔多瓦": "MDA",
    "塞浦路斯": "CYP",
    "马耳他": "MLT",
    "冰岛": "ISL",
    "爱尔兰": "IRL",
    "孟加拉": "BGD",
    "捷克": "CZE",
    "立陶宛": "LTU",
    "吉尔吉斯斯坦": "KGZ",
    "塞尔维亚": "SRB",
    "白俄罗斯": "BLR",
    "拉脱维亚": "LVA",
    "希腊": "GRC",
    "匈牙利": "HUN",
    "北马其顿": "MKD",
    "苏格兰": "GBR",
    "英格兰": "GBR",
    "威尔士": "GBR",
    }
    
    valid_countries = {}
    for country in countries:
        if country in country_code_mapping:
            valid_countries[country] = country_code_mapping[country]
        else:
            print(f"跳过: 未找到国家 '{country}' 的代码映射")
    
    if not valid_countries:
        print("错误: 没有有效的国家代码")
        return {}
    
    try:
        indicator = 'NY.GDP.PCAP.CD'
        
        df = wb.data.DataFrame(
            indicator,
            economy=list(valid_countries.values()),
            time=year,
            skipBlanks=True,
            columns='time'
        )
        
        if df.empty:
            print("警告: 未获取到任何数据")
            return {}
        
        results = {}
        year_str = f'YR{year}'
        
        for country_name, country_code in valid_countries.items():
            if country_code in df.index:
                value = df.loc[country_code, year_str]
                if pd.notna(value):
                    results[country_name] = float(value)
                else:
                    results[country_name] = None
            else:
                results[country_name] = None
        
        return results
        
    except Exception as e:
        print(f"批量获取GDP数据时出错: {e}")
        return {}

def process_json_file(input_file: str, output_file: str, target_year: int = 2022):
    """
    处理JSON文件，只添加gdp_per_capita属性
    """
    try:
        # 读取原始JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"成功读取 {len(data)} 条记录")
        
        # 收集所有需要查询的国家（去重）
        countries = set()
        for item in data:
            country = item.get('country')
            if country:
                countries.add(country)
        
        print(f"需要查询的国家: {list(countries)}")
        
        # 批量获取GDP数据
        gdp_data = get_multiple_countries_gdp(list(countries), target_year)
        
        # 处理每条记录
        processed_data = []
        stats = {'success': 0, 'failed': 0}
        
        for i, item in enumerate(data, 1):
            country = item.get('country', '')
            company_name = item.get('name', f'记录{i}')
            
            # 创建新记录，只包含需要的四个属性
            new_item = {
                'name': item.get('name', ''),
                'city': item.get('city', ''),
                'country': country,
                'gdp_per_capita': None  # 默认值
            }
            
            if country and country in gdp_data:
                gdp_value = gdp_data[country]
                if gdp_value is not None:
                    new_item['gdp_per_capita'] = gdp_value
                    stats['success'] += 1
                    print(f"✓ {company_name}: {country} - ${gdp_value:,.2f}")
                else:
                    stats['failed'] += 1
                    print(f"✗ {company_name}: {country} - 数据不可用")
            else:
                if country:
                    stats['failed'] += 1
                    print(f"⚠ {company_name}: {country} - 未找到GDP数据")
            
            processed_data.append(new_item)
        
        # 保存到新JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
        # 打印统计信息
        print(f"\n{'='*60}")
        print("处理完成！")
        print(f"输入文件: {input_file}")
        print(f"输出文件: {output_file}")
        print(f"处理记录数: {len(data)}")
        print(f"成功获取GDP数据: {stats['success']} 条")
        print(f"未能获取GDP数据: {stats['failed']} 条")
            
        # 显示结果示例
        print(f"\n{'='*60}")
        print("结果示例（前5条）:")
        for i, item in enumerate(processed_data[:5], 1):
            gdp = item.get('gdp_per_capita')
            gdp_str = f"${gdp:,.2f}" if gdp is not None else "null"
            print(f"{i}. {item.get('name'):<20} {item.get('country'):<10} {gdp_str}")
            
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except json.JSONDecodeError:
        print(f"错误: {input_file} 不是有效的JSON格式")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")



# 主程序
if __name__ == "__main__":
    # 配置参数
    input_filename = "companies.json"      # 输入JSON文件名
    output_filename = "companies_with_gdp.json"  # 输出JSON文件名
    target_year = 2022                     # 目标年份
    
    print("=" * 60)
    print("世界银行人均GDP数据获取工具")
    print("输出格式: name, city, country, gdp_per_capita")
    print("=" * 60)
    
    # 检查输入文件
    try:
        with open(input_filename, 'r', encoding='utf-8'):
            print(f"✓ 找到输入文件: {input_filename}")
    except FileNotFoundError:
        print(f"⚠ 未找到输入文件 {input_filename}")
    
    # 处理JSON文件
    print("\n" + "=" * 60)
    print("开始处理数据...")
    process_json_file(input_filename, output_filename, target_year)
    
    print("\n" + "=" * 60)
    print("程序执行完成！")
    print("=" * 60)