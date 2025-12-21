#!/usr/bin/env python3

"""
简单测试ESM模型是否能正常加载和使用
"""

try:
    print("Testing ESM model loading...")
    import esm
    
    # 尝试加载一个小型模型
    model_name = "esm2_t6_8M_UR50D"
    if hasattr(esm.pretrained, model_name):
        print(f"✓ Found model {model_name}")
        
        # 尝试加载模型
        model_func = getattr(esm.pretrained, model_name)
        model, alphabet = model_func()
        print(f"✓ Model {model_name} loaded successfully")
        
        # 测试基本功能
        sequence = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
        batch_converter = alphabet.get_batch_converter()
        
        data = [("protein", sequence)]
        batch_labels, batch_strs, batch_tokens = batch_converter(data)
        
        print(f"✓ Batch conversion works, tokens shape: {batch_tokens.shape}")
        print("\nAll tests passed!")
    else:
        print(f"✗ Model {model_name} not found in esm.pretrained")
        print("Available models:")
        for attr in dir(esm.pretrained):
            if attr.startswith("esm2_") or attr.startswith("esm1_"):
                print(f"  - {attr}")
                
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()