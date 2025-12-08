import json
import os
import glob

def merge_json_files(output_filename="merged.json"):
    """
    将当前文件夹下的所有JSON文件合并成一个JSON对象
    
    Args:
        output_filename (str): 输出的合并文件名
    """
    
    # 获取当前文件夹路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找当前文件夹下所有的json文件
    json_files = glob.glob(os.path.join(current_dir, "*.json"))
    
    # 移除输出文件本身，避免循环引用
    output_path = os.path.join(current_dir, output_filename)
    if output_path in json_files:
        json_files.remove(output_path)
    
    if not json_files:
        print("当前文件夹中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件:")
    for file in json_files:
        print(f"  - {os.path.basename(file)}")
    
    merged_data = {}
    
    # 读取并合并所有JSON文件
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 如果数据是字典，直接合并到主字典中
                if isinstance(data, dict):
                    merged_data.update(data)
                # 如果数据是列表，检查列表中的元素是否为字典然后合并
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            merged_data.update(item)
                else:
                    # 对于其他类型，使用文件名作为键
                    filename = os.path.splitext(os.path.basename(json_file))[0]
                    merged_data[filename] = data
                    
            print(f"成功读取: {os.path.basename(json_file)}")
            
        except Exception as e:
            print(f"读取文件 {json_file} 时出错: {str(e)}")
    
    # 将合并后的数据写入输出文件
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n合并完成！输出文件: {output_filename}")
        print(f"总共合并了 {len(merged_data)} 个地点")
        
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")

def merge_json_files_object(output_filename="merged.json"):
    """
    专门针对对象合并的方法：将所有JSON文件中的对象属性合并到一个大对象中
    
    Args:
        output_filename (str): 输出的合并文件名
    """
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_files = glob.glob(os.path.join(current_dir, "*.json"))
    
    output_path = os.path.join(current_dir, output_filename)
    if output_path in json_files:
        json_files.remove(output_path)
    
    if not json_files:
        print("当前文件夹中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件:")
    for file in json_files:
        print(f"  - {os.path.basename(file)}")
    
    merged_data = {}
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 处理不同的数据结构
                if isinstance(data, dict):
                    # 直接合并字典
                    merged_data.update(data)
                elif isinstance(data, list):
                    # 处理列表，提取其中的字典对象
                    for item in data:
                        if isinstance(item, dict):
                            merged_data.update(item)
                
            print(f"成功处理: {os.path.basename(json_file)}")
            
        except Exception as e:
            print(f"处理文件 {json_file} 时出错: {str(e)}")
    
    # 写入合并后的文件
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n对象合并完成！输出文件: {output_filename}")
        print(f"总共合并了 {len(merged_data)} 个地点")
        print("合并后的格式示例:")
        if merged_data:
            first_key = list(merged_data.keys())[0]
            print(f'  "{first_key}": {json.dumps(merged_data[first_key], ensure_ascii=False)}')
        
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")

if __name__ == "__main__":
    # 使用方法：对象合并
    merge_json_files_object("cities.json")