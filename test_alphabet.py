#!/usr/bin/env python3

"""
测试ESM模型的alphabet对象结构
"""

try:
    import esm
    
    # 加载模型
    model_name = "esm2_t6_8M_UR50D"
    model_func = getattr(esm.pretrained, model_name)
    model, alphabet = model_func()
    
    # 查看alphabet对象的属性
    print("Alphabet attributes:")
    for attr in dir(alphabet):
        if not attr.startswith("_"):
            print(f"  - {attr}")
    
    # 查看mask相关属性
    print("\nMask related:")
    print(f"  - mask_idx: {alphabet.mask_idx}")
    
    # 查看tokens属性
    if hasattr(alphabet, "tokens"):
        print(f"  - tokens: {alphabet.tokens[:20]}...")
        if alphabet.mask_idx < len(alphabet.tokens):
            print(f"  - mask_token: {alphabet.tokens[alphabet.mask_idx]}")
    
    # 查看vocab属性
    if hasattr(alphabet, "vocab"):
        print(f"  - vocab size: {len(alphabet.vocab)}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
