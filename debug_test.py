import requests
import json
import os

# 测试UniProt ID
TEST_UNIPROT_ID = "P68871"  # Human hemoglobin subunit beta

print(f"Testing with UniProt ID: {TEST_UNIPROT_ID}")
print("=" * 60)

# 1. 测试AlphaFold API请求
print("1. Testing AlphaFold API request...")
api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{TEST_UNIPROT_ID}"

# 直接使用requests测试API请求
response = requests.get(api_url, timeout=(5, 60))
print(f"   HTTP Status Code: {response.status_code}")
print(f"   Response Body Length: {len(response.text)}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"   Number of predictions: {len(data)}")
        
        # 解析selected_prediction
        if data:
            target_entry_id = f"AF-{TEST_UNIPROT_ID}-F1"
            selected_prediction = None
            
            # 优先选择entryId匹配的条目
            for pred in data:
                if pred.get("entryId") == target_entry_id:
                    selected_prediction = pred
                    break
            
            # 如果没有找到entryId匹配的，尝试匹配modelEntityId
            if not selected_prediction:
                for pred in data:
                    if pred.get("modelEntityId") == TEST_UNIPROT_ID:
                        selected_prediction = pred
                        break
            
            # 如果还是没有找到，使用第一个条目
            if not selected_prediction:
                selected_prediction = data[0]
            
            print("   Selected Prediction:")
            print(f"      entryId: {selected_prediction.get('entryId')}")
            print(f"      modelEntityId: {selected_prediction.get('modelEntityId')}")
            print(f"      pdbUrl: {selected_prediction.get('pdbUrl')}")
            print(f"      cifUrl: {selected_prediction.get('cifUrl')}")
            
            # 测试下载模型文件
            model_url = selected_prediction.get('pdbUrl') or selected_prediction.get('cifUrl')
            if model_url:
                print("\n2. Testing model file download...")
                response = requests.head(model_url, timeout=(5, 60))
                print(f"   HTTP Status Code: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                print(f"   File Extension: {os.path.splitext(model_url)[1]}")
    except json.JSONDecodeError as e:
        print(f"   JSON Decode Error: {e}")
        print(f"   Response Text: {response.text[:500]}...")

print("\n" + "=" * 60)
print("Debug test completed!")
