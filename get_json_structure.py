

import ijson
import json
from collections import OrderedDict
import sys
import argparse
import glob

def get_value_type(value):
    """回傳值的基本型別字串"""
    if isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, int):
        return 'integer'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, str):
        return 'string'
    elif isinstance(value, list):
        return 'array'
    elif isinstance(value, dict):
        return 'object'
    elif value is None:
        return 'null'
    else:
        return 'unknown'

def analyze_structure(obj):
    """遞迴分析物件的結構"""
    structure = OrderedDict()
    for key, value in obj.items():
        value_type = get_value_type(value)
        if value_type == 'object':
            # 如果是巢狀物件，就遞迴分析下去
            structure[key] = analyze_structure(value)
        elif value_type == 'array' and value:
            # 如果是陣列，分析陣列中第一個元素的結構
            first_item_type = get_value_type(value[0])
            if first_item_type == 'object':
                structure[key] = [analyze_structure(value[0])]
            else:
                structure[key] = [first_item_type]
        else:
            structure[key] = value_type
    return structure

def find_json_file():
    """Automatically find a single .json file in the current directory."""
    json_files = glob.glob('*.json')
    if len(json_files) == 1:
        return json_files[0]
    elif len(json_files) == 0:
        print("Error: No JSON file found in the current directory.", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Error: Multiple JSON files found: {', '.join(json_files)}", file=sys.stderr)
        print("Please specify which one to process by running: python get_json_structure.py <filename>", file=sys.stderr)
        sys.exit(1)

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="Analyze the structure of the first object in an Open WebUI JSON export.")
    parser.add_argument('json_file', nargs='?', default=None, 
                        help="Path to the JSON file to process. If not provided, the script will look for a single .json file in the current directory.")
    args = parser.parse_args()

    if args.json_file:
        json_file_path = args.json_file
    else:
        json_file_path = find_json_file()

    try:
        with open(json_file_path, 'rb') as f:
            # ijson.items 會以串流方式尋找頂層陣列中的物件
            # 'item' 假設 JSON 的根是一個陣列，例如: [ {...}, {...}, ... ]
            objects = ijson.items(f, 'item')
            
            # 取得第一個物件
            first_obj = next(objects)
            
            print(f"成功讀取 \"{json_file_path}\" 中的第一個物件，開始分析結構...")
            
            # 分析結構
            structure = analyze_structure(first_obj)
            
            print("\nJSON 結構分析結果:")
            print("=" * 20)
            # 使用 json.dumps 來美化輸出
            print(json.dumps(structure, indent=2, ensure_ascii=False))
            print("=" * 20)
            print("\n注意：此結構是基於檔案中的第一個聊天記錄物件分析得出的。")

    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 \"{json_file_path}\"", file=sys.stderr)
    except StopIteration:
        print("錯誤: JSON 檔案中似乎沒有找到任何項目。它可能是一個空陣列或格式不符.", file=sys.stderr)
    except Exception as e:
        print(f"發生未預期的錯誤: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()

