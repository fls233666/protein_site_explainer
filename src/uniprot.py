import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
from urllib.parse import urlparse
import time
from .cache import disk_cache

# UniProt REST API端点
UNIPROT_API_URL = "https://rest.uniprot.org/uniprotkb/{}.xml"

# 创建统一的requests.Session对象，用于所有网络请求
def create_session(timeout=30, max_retries=3, backoff_factor=0.5):
    """创建带超时、重试和指数退避的requests.Session
    
    Args:
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        backoff_factor: 指数退避因子
    
    Returns:
        requests.Session: 配置好的Session对象
    """
    session = requests.Session()
    
    # 设置默认超时
    session.timeout = timeout
    
    # 设置User-Agent
    session.headers.update({
        "User-Agent": "ProteinSiteExplainer/1.0 (+https://github.com/yourusername/protein_site_explainer)"
    })
    
    # 添加重试策略
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]  # 只对GET和HEAD请求重试
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    
    # 为所有HTTP和HTTPS请求添加适配器
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# 创建全局Session对象
_session = create_session()

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
    
    try:
        response = _session.get(url)
        response.raise_for_status()  # 检查请求是否成功
    except requests.exceptions.HTTPError as e:
        # 处理特定错误
        if response.status_code == 429:
            raise requests.exceptions.HTTPError(f"Too many requests to UniProt API for ID {uniprot_id}. Please try again later.")
        elif response.status_code == 404:
            raise requests.exceptions.HTTPError(f"UniProt ID {uniprot_id} not found.")
        else:
            raise requests.exceptions.HTTPError(f"Failed to fetch UniProt data for ID {uniprot_id}: HTTP {response.status_code} - {response.reason}")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Network error when fetching UniProt data for ID {uniprot_id}: {str(e)}")
    
    # 解析XML响应
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse UniProt XML response for ID {uniprot_id}: {str(e)}")
    
    # 命名空间
    ns = {
        "uniprot": "http://uniprot.org/uniprot",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance"
    }
    
    # 提取序列 - 查找所有序列元素并选择包含有效文本的元素
    sequence_elements = root.findall(".//uniprot:sequence", ns)
    if not sequence_elements:
        raise ValueError(f"No sequence elements found for UniProt ID: {uniprot_id}")
    
    sequence = ""
    for seq_elem in sequence_elements:
        if seq_elem.text is not None:
            sequence = seq_elem.text.strip()
            if sequence:
                break  # 找到第一个非空序列就返回
    
    if not sequence:
        raise ValueError(f"Empty sequence found for UniProt ID: {uniprot_id}")
    
    # 提取特征
    features = []
    for feature_elem in root.findall(".//uniprot:feature", ns):
        feature_type = feature_elem.attrib.get("type")
        if not feature_type:
            continue
        
        # 获取位置信息 - 兼容begin/end和position两种格式
        location_elem = feature_elem.find(".//uniprot:location", ns)
        if location_elem is None:
            continue
        
        # 尝试获取begin和end元素
        begin_elem = location_elem.find(".//uniprot:begin", ns)
        end_elem = location_elem.find(".//uniprot:end", ns)
        
        start = end = 0
        
        # 处理begin/end格式
        if begin_elem is not None and end_elem is not None:
            try:
                start = int(begin_elem.attrib.get("position", "0"))
                end = int(end_elem.attrib.get("position", "0"))
            except ValueError:
                continue
        # 处理单个position格式
        else:
            position_elem = location_elem.find(".//uniprot:position", ns)
            if position_elem is not None:
                try:
                    start = end = int(position_elem.attrib.get("position", "0"))
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
