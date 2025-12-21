#!/usr/bin/env python3
"""
测试缓存装饰器功能的脚本
"""
import os
import sys
import time
from datetime import timedelta
from src.cache import disk_cache

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@disk_cache(duration=timedelta(seconds=0.1))  # 短期缓存，方便测试
def test_function(x):
    """测试函数，模拟耗时操作"""
    print(f"执行test_function({x})...")
    time.sleep(0.1)  # 模拟耗时
    return x * 2

if __name__ == "__main__":
    print("=== 测试缓存装饰器 ===")
    
    # 第一次调用，应该执行函数
    print("第一次调用 test_function(5):")
    result1 = test_function(5)
    print(f"结果: {result1}")
    
    # 第二次调用，应该使用缓存
    print("\n第二次调用 test_function(5):")
    result2 = test_function(5)
    print(f"结果: {result2}")
    
    # 等待缓存过期
    print("\n等待0.2秒让缓存过期...")
    time.sleep(0.2)
    
    # 第三次调用，应该再次执行函数
    print("\n第三次调用 test_function(5):")
    result3 = test_function(5)
    print(f"结果: {result3}")
    
    print("\n=== 测试完成 ===")
