import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
from .cache import disk_cache

# UniProt REST API端点
UNIPROT_API_URL = "https://rest.uniprot.org/uniprotkb/{}.xml"

class UniProtEntry:
    """UniProt条目数据类"""
    def __init__(self, uniprot_id, sequence, features):
        self.uniprot_id = uniprot_id
        self.sequence = sequence
        self.features = features  # 列表 of Feature 对象

class Feature:
    """UniProt特征数据类"""
    def __init__(self, type, description, start, end, evidence=None):
        self.type = type
        self.description = description
        self.start = start  # 1-based
        self.end = end      # 1-based
        self.evidence = evidence
    
    def __str__(self):
        return f"{self.type}: {self.description} [{self.start}-{self.end}]"
    
    def __repr__(self):
        return f"Feature(type='{self.type}', description='{self.description}', start={self.start}, end={self.end})"

def get_uniprot_entry(uniprot_id):
    """获取UniProt条目信息
    
    Args:
        uniprot_id: UniProt ID字符串
    
    Returns:
        UniProtEntry 对象
    
    Raises:
        requests.exceptions.HTTPError: 如果API请求失败
    """
    return _fetch_uniprot_data(uniprot_id)

@disk_cache(duration=timedelta(days=30))
def _fetch_uniprot_data(uniprot_id):
    """从UniProt API获取数据（私有函数，带缓存）"""
    url = UNIPROT_API_URL.format(uniprot_id)
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功
    
    # 解析XML响应
    root = ET.fromstring(response.content)
    
    # 命名空间
    ns = {
        "uniprot": "http://uniprot.org/uniprot",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance"
    }
    
    # 提取序列
    sequence_elem = root.find(".//uniprot:sequence", ns)
    if sequence_elem is None:
        raise ValueError(f"No sequence found for UniProt ID: {uniprot_id}")
    
    sequence = sequence_elem.text.strip()
    
    # 提取特征
    features = []
    for feature_elem in root.findall(".//uniprot:feature", ns):
        feature_type = feature_elem.attrib.get("type")
        if not feature_type:
            continue
        
        # 获取位置信息
        location_elem = feature_elem.find(".//uniprot:location/uniprot:begin", ns)
        end_elem = feature_elem.find(".//uniprot:location/uniprot:end", ns)
        
        if location_elem is None or end_elem is None:
            continue
        
        try:
            start = int(location_elem.attrib.get("position", "0"))
            end = int(end_elem.attrib.get("position", "0"))
        except ValueError:
            continue
        
        if start <= 0 or end <= 0:
            continue
        
        # 获取描述
        description = ""
        desc_elem = feature_elem.find(".//uniprot:description", ns)
        if desc_elem is not None and desc_elem.text:
            description = desc_elem.text.strip()
        
        # 创建Feature对象
        feature = Feature(
            type=feature_type,
            description=description,
            start=start,
            end=end
        )
        features.append(feature)
    
    return UniProtEntry(uniprot_id, sequence, features)

def get_features_at_position(features, position):
    """获取特定位置的所有特征
    
    Args:
        features: Feature 对象列表
        position: 1-based 位置
    
    Returns:
        list of Feature 对象
    """
    return [feature for feature in features if feature.start <= position <= feature.end]

def map_features_to_mutations(mutations, features):
    """将特征映射到突变位置
    
    Args:
        mutations: Mutation 对象列表
        features: Feature 对象列表
    
    Returns:
        dict: 突变位置 -> 特征列表
    """
    feature_map = {}
    
    for mutation in mutations:
        position_features = get_features_at_position(features, mutation.position)
        feature_map[mutation.position] = position_features
    
    return feature_map

def format_features_for_display(features):
    """格式化特征列表用于显示
    
    Args:
        features: Feature 对象列表
    
    Returns:
        str: 格式化的特征字符串
    """
    if not features:
        return "None"
    
    return "; ".join([f"{f.type}: {f.description}" for f in features])
