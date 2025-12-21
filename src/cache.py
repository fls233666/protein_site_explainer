import os
import time
import joblib
from datetime import timedelta
from functools import wraps

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)

def disk_cache(duration=timedelta(days=7), ignore_args=None):
    """磁盘缓存装饰器
    
    Args:
        duration: 缓存有效期
        ignore_args: 忽略的参数索引列表
    """
    def decorator(func):
        # 创建函数特定的缓存目录
        func_cache_dir = os.path.join(CACHE_DIR, func.__name__)
        os.makedirs(func_cache_dir, exist_ok=True)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 构建缓存键
            if ignore_args:
                filtered_args = tuple(arg for i, arg in enumerate(args) if i not in ignore_args)
            else:
                filtered_args = args
            
            cache_key = joblib.hash((filtered_args, frozenset(kwargs.items())))
            cache_file = os.path.join(func_cache_dir, f"{cache_key}.joblib")
            
            # 检查缓存是否存在且有效
            if os.path.exists(cache_file):
                cache_info = joblib.load(cache_file)
                if (cache_info["timestamp"] + duration.total_seconds()) > time.time():
                    return cache_info["result"]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_info = {
                "timestamp": time.time(),
                "result": result
            }
            # 再次确保目录存在，增加健壮性
            os.makedirs(func_cache_dir, exist_ok=True)
            joblib.dump(cache_info, cache_file)
            
            return result
        
        return wrapper
    
    return decorator

def clear_cache():
    """清除所有缓存"""
    if os.path.exists(CACHE_DIR):
        import shutil
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR, exist_ok=True)
