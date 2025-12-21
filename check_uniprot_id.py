import requests

uniprot_id = "P0DTC2"
url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.xml"

try:
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Reason: {response.reason}")
    
    if response.status_code == 200:
        print(f"UniProt ID {uniprot_id} exists!")
    else:
        print(f"UniProt ID {uniprot_id} not found!")
        
    # 尝试使用另一个已知存在的ID进行测试
    test_id = "P0DTC1"
    test_url = f"https://rest.uniprot.org/uniprotkb/{test_id}.xml"
    test_response = requests.get(test_url)
    print(f"\nTest with ID {test_id}:")
    print(f"Status code: {test_response.status_code}")
    print(f"Reason: {test_response.reason}")
    
except Exception as e:
    print(f"Error: {e}")
