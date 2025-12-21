import requests
import xml.etree.ElementTree as ET

uniprot_id = "P0DTC2"
url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.xml"

try:
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Reason: {response.reason}")
    
    if response.status_code == 200:
        print(f"UniProt ID {uniprot_id} exists!")
        
        # 保存XML响应以便检查
        with open(f"{uniprot_id}_response.xml", "wb") as f:
            f.write(response.content)
        print(f"XML response saved to {uniprot_id}_response.xml")
        
        # 尝试解析XML
        try:
            root = ET.fromstring(response.content)
            print("XML parsing successful!")
            
            # 命名空间
            ns = {
                "uniprot": "http://uniprot.org/uniprot",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance"
            }
            
            # 尝试提取序列
            sequence_elem = root.find(".//uniprot:sequence", ns)
            if sequence_elem is not None:
                sequence = sequence_elem.text.strip()
                print(f"Sequence length: {len(sequence)}")
                print(f"Sequence start: {sequence[:20]}...")
            else:
                print("No sequence found!")
                
                # 打印所有元素名称以了解结构
                print("\nAll element tags in XML:")
                for elem in root.iter():
                    print(elem.tag)
            
            # 尝试提取特征
            features = []
            for feature_elem in root.findall(".//uniprot:feature", ns):
                feature_type = feature_elem.attrib.get("type")
                if feature_type:
                    features.append(feature_type)
            
            print(f"\nFound {len(features)} features")
            if features:
                print(f"Feature types: {set(features)}")
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            print("Response content (first 500 chars):")
            print(response.content[:500])
    
    else:
        print(f"UniProt ID {uniprot_id} not found!")
        print(f"Response content: {response.content}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
