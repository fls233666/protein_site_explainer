import esm
print("ESM module contents:", dir(esm))
print("ESM version:", getattr(esm, '__version__', 'unknown'))

# 检查是否有pretrained函数
if hasattr(esm, 'pretrained'):
    print("Has pretrained function!")
    print("Type of esm.pretrained:", type(esm.pretrained))
    print("Dir of esm.pretrained:", dir(esm.pretrained))
    
    # 尝试调用pretrained函数来获取模型列表
    try:
        models = esm.pretrained()
        print("Pretrained function returned:", models)
    except Exception as e:
        print("Error calling pretrained:", e)
else:
    print("No pretrained function found.")

# 检查是否有其他相关的属性
for attr in ['ESM2', 'Model', 'ProteinBertModel']:
    if hasattr(esm, attr):
        print(f"Has {attr}: {getattr(esm, attr)}")
