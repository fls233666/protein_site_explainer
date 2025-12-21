import os
import time
import joblib
import tempfile
import hashlib
import threading
from datetime import timedelta
from functools import wraps
from pathlib import Path

# 默认缓存目录
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")

# 确保缓存目录存在
os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)

# 缓存版本号 - 当代码或模型版本变化时，更新此版本号
CACHE_VERSION = "v1.0"

# 缓存文件锁
_cache_locks = {}
_lock_lock = threading.Lock()

def _get_lock(cache_file):
    """获取缓存文件的锁"""
    with _lock_lock:
        if cache_file not in _cache_locks:
            _cache_locks[cache_file] = threading.Lock()
        return _cache_locks[cache_file]

def disk_cache(duration=timedelta(days=7), ignore_args=None, cache_dir=None, max_size=None, ttl=None):
    """磁盘缓存装饰器
    
    Args:
        duration: 缓存有效期
        ignore_args: 忽略的参数索引列表
        cache_dir: 自定义缓存目录，默认为项目根目录下的.cache
        max_size: 最大缓存大小（字节），超过则清理旧缓存
        ttl: 可选的TTL（生存时间），优先级高于duration
    """
    # 使用自定义缓存目录或默认目录
    base_cache_dir = cache_dir or DEFAULT_CACHE_DIR
    
    def decorator(func):
        # 创建函数特定的缓存目录
        func_cache_dir = os.path.join(base_cache_dir, func.__name__)
        os.makedirs(func_cache_dir, exist_ok=True)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 构建缓存键
            if ignore_args:
                filtered_args = tuple(arg for i, arg in enumerate(args) if i not in ignore_args)
            else:
                filtered_args = args
            
            # 包含缓存版本号以确保版本变化时缓存失效
            cache_key_data = (CACHE_VERSION, filtered_args, frozenset(kwargs.items()))
            cache_key = joblib.hash(cache_key_data)
            cache_file = os.path.join(func_cache_dir, f"{cache_key}.joblib")
            
            # 检查缓存是否存在且有效
            if os.path.exists(cache_file):
                with _get_lock(cache_file):
                    cache_info = joblib.load(cache_file)
                    expire_time = cache_info["timestamp"] + (ttl or duration.total_seconds())
                    if expire_time > time.time():
                        return cache_info["result"]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_info = {
                "timestamp": time.time(),
                "result": result,
                "version": CACHE_VERSION
            }
            
            # 并发安全的缓存写入（使用临时文件 + 原子重命名）
            with _get_lock(cache_file):
                # 再次确保目录存在，增加健壮性
                os.makedirs(func_cache_dir, exist_ok=True)
                
                # 使用临时文件写入
                with tempfile.NamedTemporaryFile(dir=func_cache_dir, suffix=".joblib", delete=False) as tmp_file:
                    tmp_file_path = tmp_file.name
                    joblib.dump(cache_info, tmp_file_path)
                
                # 原子重命名替换旧文件
                os.replace(tmp_file_path, cache_file)
            
            # 如果设置了最大大小，检查并清理缓存
            if max_size:
                _cleanup_cache(func_cache_dir, max_size)
            
            return result
        
        return wrapper
    
    return decorator

def _cleanup_cache(cache_dir, max_size):
    """清理缓存以保持在最大大小以内"""
    # 获取所有缓存文件及其大小和修改时间
    cache_files = []
    total_size = 0
    
    for filename in os.listdir(cache_dir):
        if filename.endswith(".joblib"):
            file_path = os.path.join(cache_dir, filename)
            try:
                file_size = os.path.getsize(file_path)
                mtime = os.path.getmtime(file_path)
                cache_files.append((file_path, file_size, mtime))
                total_size += file_size
            except OSError:
                # 忽略无法访问的文件
                continue
    
    # 如果总大小超过最大大小，清理旧文件
    if total_size > max_size:
        # 按修改时间排序（最旧的先删除）
        cache_files.sort(key=lambda x: x[2])
        
        # 删除旧文件直到总大小在限制以内
        for file_path, file_size, _ in cache_files:
            if total_size <= max_size:
                break
            try:
                os.remove(file_path)
                total_size -= file_size
            except OSError:
                # 忽略无法删除的文件
                continue

def clear_cache(cache_dir=None):
    """清除所有缓存
    
    Args:
        cache_dir: 要清除的缓存目录，默认为默认缓存目录
    """
    cache_dir_to_clear = cache_dir or DEFAULT_CACHE_DIR
    if os.path.exists(cache_dir_to_clear):
        import shutil
        shutil.rmtree(cache_dir_to_clear)
        os.makedirs(cache_dir_to_clear, exist_ok=True)

def get_cache_size(cache_dir=None):
    """获取缓存总大小
    
    Args:
        cache_dir: 要检查的缓存目录，默认为默认缓存目录
    
    Returns:
        int: 缓存总大小（字节）
    """
    cache_dir_to_check = cache_dir or DEFAULT_CACHE_DIR
    total_size = 0
    
    for root, _, files in os.walk(cache_dir_to_check):
        for file in files:
            if file.endswith(".joblib"):
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    # 忽略无法访问的文件
                    continue
    
    return total_size
