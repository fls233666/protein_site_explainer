import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

from src.uniprot import get_uniprot_entry

uniprot_id = "P0DTC2"

try:
    print(f"Trying to get UniProt entry for ID: {uniprot_id}")
    entry = get_uniprot_entry(uniprot_id)
    print(f"Success! Got entry for {uniprot_id}")
    print(f"Sequence length: {len(entry.sequence)}")
    print(f"Number of features: {len(entry.features)}")
    
    # 尝试获取一些特征
    if entry.features:
        print(f"First few features: {entry.features[:3]}")
    
    # 测试另一个ID
    test_id = "P0DTC1"
    print(f"\nTrying to get UniProt entry for ID: {test_id}")
    test_entry = get_uniprot_entry(test_id)
    print(f"Success! Got entry for {test_id}")
    print(f"Sequence length: {len(test_entry.sequence)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
