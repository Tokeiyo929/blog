import json
import os
import glob

def merge_json_files(output_filename="merged.json"):
    """
    将当前文件夹下的所有JSON文件合并成一个JSON文件
    
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
    
    merged_data = []
    
    # 读取并合并所有JSON文件
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 如果数据是列表，则扩展到合并数据中
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
                    
            print(f"成功读取: {os.path.basename(json_file)}")
            
        except Exception as e:
            print(f"读取文件 {json_file} 时出错: {str(e)}")
    
    # 将合并后的数据写入输出文件
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n合并完成！输出文件: {output_filename}")
        print(f"总共合并了 {len(merged_data)} 条数据")
        
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")

def merge_json_files_alternative(output_filename="merged.json", merge_method="object"):
    """
    另一种合并方式：可以选择按对象或数组合并
    
    Args:
        output_filename (str): 输出的合并文件名
        merge_method (str): 合并方式 - "array" 或 "object"
    """
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_files = glob.glob(os.path.join(current_dir, "*.json"))
    
    output_path = os.path.join(current_dir, output_filename)
    if output_path in json_files:
        json_files.remove(output_path)
    
    if not json_files:
        print("当前文件夹中没有找到JSON文件")
        return
    
    if merge_method == "array":
        # 方法1：将所有JSON文件内容合并成一个数组
        merged_data = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        merged_data.append(data)
                        
                print(f"成功读取: {os.path.basename(json_file)}")
                
            except Exception as e:
                print(f"读取文件 {json_file} 时出错: {str(e)}")
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
    elif merge_method == "object":
        # 方法2：将所有JSON文件内容合并成一个对象，文件名作为键
        merged_data = {}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    filename = os.path.splitext(os.path.basename(json_file))[0]
                    merged_data[filename] = data
                    
                print(f"成功读取: {os.path.basename(json_file)}")
                
            except Exception as e:
                print(f"读取文件 {json_file} 时出错: {str(e)}")
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n合并完成！输出文件: {output_filename}")

if __name__ == "__main__":
    # 使用方法1：简单的数组合并
    merge_json_files("companies.json")
    
    print("\n" + "="*50 + "\n")
    
    # 使用方法2：可选择合并方式
    # merge_json_files_alternative("merged_array.json", "array")
    # merge_json_files_alternative("merged_object.json", "object")