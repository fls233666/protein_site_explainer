import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

from src.alphafold import get_alphafold_data
import requests.exceptions

uniprot_id = "P0DTC2"

try:
    print(f"Trying to get AlphaFold data for ID: {uniprot_id}")
    alphafold_data = get_alphafold_data(uniprot_id)
    print(f"Success! Got AlphaFold data for {uniprot_id}")
    print(f"Number of pLDDT scores: {len(alphafold_data.plddt_scores)}")
    
    # 尝试获取一些pLDDT分数
    if alphafold_data.plddt_scores:
        print(f"First few pLDDT scores: {alphafold_data.plddt_scores[:3]}")
        
        # 测试get_plddt_at_position
        test_positions = [100, 200, 300]
        for pos in test_positions:
            plddt = alphafold_data.get_plddt_at_position(pos)
            print(f"pLDDT at position {pos}: {plddt}")

except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Status code: {e.response.status_code}")
    print(f"Reason: {e.response.reason}")
except Exception as e:
    print(f"Other Error: {e}")
    import traceback
    traceback.print_exc()
