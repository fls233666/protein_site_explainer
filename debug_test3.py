import os
import py3Dmol
from src.alphafold import download_pdb

# 测试UniProt ID
TEST_UNIPROT_ID = "P68871"  # Human hemoglobin subunit beta

print("=" * 60)
print("4. Testing 3D structure rendering...")
print("   Note: Full 3D rendering test requires running Streamlit app.")
print("   Testing model file parsing...")

try:
    # 尝试创建3D结构
    pdb_file = download_pdb(TEST_UNIPROT_ID)
    file_extension = os.path.splitext(pdb_file)[1].lower()
    print(f"   File Extension: {file_extension}")
    
    # 简单测试py3Dmol是否能加载文件
    with open(pdb_file, 'r') as f:
        file_content = f.read()
    
    file_format = 'mmcif' if file_extension in ['.cif', '.mmcif'] else 'pdb'
    
    view = py3Dmol.view(width=800, height=600)
    view.addModel(file_content, file_format)
    view.setStyle({"cartoon": {"color": "spectrum"}})
    view.zoomTo()
    
    print("   py3Dmol model loaded successfully!")
    
    # 测试当前的颜色方案 - 可能有问题的部分
    print("   Testing current color scheme (with pLDDT parameter)...")
    try:
        view2 = py3Dmol.view(width=800, height=600)
        view2.addModel(file_content, file_format)
        view2.setStyle({"cartoon": {"color": "spectrum", "colorscheme": "pLDDT"}})
        view2.zoomTo()
        print("   Color scheme 'pLDDT' applied successfully")
    except Exception as e:
        print(f"   Color scheme 'pLDDT' failed: {type(e).__name__}: {e}")
        print("   This might be the cause of 3D rendering issues")
        
    # 测试建议的颜色方案 - 使用b-factor
    print("   Testing suggested color scheme (with b-factor)...")
    try:
        view3 = py3Dmol.view(width=800, height=600)
        view3.addModel(file_content, file_format)
        view3.setStyle({"cartoon": {"color": "spectrum", "colorscheme": {"prop": "b", "gradient": "redyellowblue", "min": 0, "max": 100}}})
        view3.zoomTo()
        print("   Color scheme with b-factor applied successfully")
    except Exception as e:
        print(f"   Color scheme with b-factor failed: {type(e).__name__}: {e}")
        
    # 测试简单颜色方案
    print("   Testing simple color scheme...")
    try:
        view4 = py3Dmol.view(width=800, height=600)
        view4.addModel(file_content, file_format)
        view4.setStyle({"cartoon": {"color": "blue"}})
        view4.zoomTo()
        print("   Simple blue color scheme applied successfully")
    except Exception as e:
        print(f"   Simple color scheme failed: {type(e).__name__}: {e}")
        
except Exception as e:
    print(f"   Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug test 3 completed!")
