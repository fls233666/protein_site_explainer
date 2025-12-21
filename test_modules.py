#!/usr/bin/env python3

# 测试各核心模块是否能正常导入和基本功能
try:
    print("Testing module imports...")
    
    # 测试解析模块
    from src.parsing import parse_mutation, parse_mutation_list
    print("✓ src.parsing imported successfully")
    
    # 测试缓存模块
    from src.cache import disk_cache
    print("✓ src.cache imported successfully")
    
    # 测试UniProt模块
    from src.uniprot import get_uniprot_entry
    print("✓ src.uniprot imported successfully")
    
    # 测试AlphaFold模块
    from src.alphafold import get_alphafold_data
    print("✓ src.alphafold imported successfully")
    
    # 测试ESM评分模块
    from src.esm_scoring import ESMScorer
    print("✓ src.esm_scoring imported successfully")
    
    # 测试解释模块
    from src.explain import Explainer
    print("✓ src.explain imported successfully")
    
    # 测试可视化模块
    from src.viz import Visualizer
    print("✓ src.viz imported successfully")
    
    # 测试Streamlit应用
    import streamlit as st
    print("✓ streamlit imported successfully")
    
    print("\nAll modules imported successfully!")
    
    # 测试简单功能
    print("\nTesting basic functionality...")
    
    # 测试解析功能
    try:
        mutation = parse_mutation("A123T")
        print(f"✓ parse_mutation: {mutation}")
        
        mutations = parse_mutation_list("A123T, K456M, R789L")
        print(f"✓ parse_mutation_list: {len(mutations)} mutations parsed")
    except Exception as e:
        print(f"✗ parse_mutation: {e}")
    
    print("\nBasic functionality tests completed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
