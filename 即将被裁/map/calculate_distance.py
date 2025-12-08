import json
import math

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    计算两个经纬度坐标之间的距离（公里）
    使用Haversine公式
    """
    # 将十进制度数转化为弧度
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine公式
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # 地球半径（公里）
    radius = 6371.0
    
    return radius * c

def find_nearby_cities(city_data, distance_threshold=40):
    """
    为每个城市查找方圆10公里内的邻近城市
    """
    cities = list(city_data.keys())
    result = {}
    
    for i, city1 in enumerate(cities):
        lat1 = city_data[city1]["lat"]
        lng1 = city_data[city1]["lng"]
        
        nearby_cities = []
        has_nearby = False
        
        for j, city2 in enumerate(cities):
            if i != j:  # 不与自己比较
                lat2 = city_data[city2]["lat"]
                lng2 = city_data[city2]["lng"]
                
                distance = calculate_distance(lat1, lng1, lat2, lng2)
                
                if distance <= distance_threshold:
                    nearby_cities.append({
                        "name": city2,
                        "distance": round(distance, 2)
                    })
                    has_nearby = True
        
        result[city1] = {
            "lat": lat1,
            "lng": lng1,
            "has_nearby_city": has_nearby,
            "nearby_cities": nearby_cities
        }
    
    return result

def main():
    # 从JSON文件加载数据
    try:
        with open('cities.json', 'r', encoding='utf-8') as f:
            city_data = json.load(f)
    except FileNotFoundError:
        print("错误：找不到cities.json文件")
        return
    except json.JSONDecodeError:
        print("错误：JSON文件格式不正确")
        return
    
    print("成功加载城市数据，开始计算邻近关系...")
    
    # 计算邻近城市
    result = find_nearby_cities(city_data)
    
    # 打印结果
    print("\n城市邻近关系分析：")
    print("=" * 50)
    
    for city, info in result.items():
        status = "有" if info['has_nearby_city'] else "无"
        print(f"{city}:")
        print(f"  经纬度: ({info['lat']}, {info['lng']})")
        print(f"  10公里内邻近城市: {status}")
        if info['nearby_cities']:
            print(f"  邻近城市列表:")
            for nearby in info['nearby_cities']:
                print(f"    - {nearby['name']}: {nearby['distance']}公里")
        print()
    
    # 保存结果到新的JSON文件
    output_file = 'cities_with_nearby.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到 '{output_file}'")
    
    # 统计信息
    total_cities = len(result)
    cities_with_nearby = sum(1 for city in result.values() if city['has_nearby_city'])
    
    print(f"\n统计信息:")
    print(f"总城市数: {total_cities}")
    print(f"有邻近城市的城市数: {cities_with_nearby}")
    print(f"无邻近城市的城市数: {total_cities - cities_with_nearby}")

if __name__ == "__main__":
    main()