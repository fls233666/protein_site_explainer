#!/usr/bin/env python3
"""
测试_fetch_uniprot_data函数的缓存功能
"""
import os
import sys
import time
from src.uniprot import get_uniprot_entry

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=== 测试_fetch_uniprot_data缓存功能 ===")
    
    uniprot_id = "P0DTC2"
    
    # 第一次调用，应该从API获取数据并缓存
    print(f"第一次调用 get_uniprot_entry({uniprot_id}):")
    start_time = time.time()
    try:
        entry1 = get_uniprot_entry(uniprot_id)
        end_time = time.time()
        print(f"成功获取数据！")
        print(f"序列长度: {len(entry1.sequence)} 氨基酸")
        print(f"耗时: {end_time - start_time:.2f} 秒")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 第二次调用，应该使用缓存
    print(f"\n第二次调用 get_uniprot_entry({uniprot_id}):")
    start_time = time.time()
    try:
        entry2 = get_uniprot_entry(uniprot_id)
        end_time = time.time()
        print(f"成功获取数据！")
        print(f"序列长度: {len(entry2.sequence)} 氨基酸")
        print(f"耗时: {end_time - start_time:.2f} 秒")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 检查缓存文件是否存在
    cache_dir = os.path.join(os.path.dirname(__file__), ".cache", "_fetch_uniprot_data")
    print(f"\n缓存目录: {cache_dir}")
    if os.path.exists(cache_dir):
        cache_files = os.listdir(cache_dir)
        print(f"缓存文件数量: {len(cache_files)}")
        if cache_files:
            print(f"第一个缓存文件: {cache_files[0]}")
    else:
        print("缓存目录不存在！")
    
    print("\n=== 测试完成 ===")
