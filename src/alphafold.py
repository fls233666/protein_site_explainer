import os
import requests
import gzip
import tempfile
from datetime import timedelta
from Bio.PDB import PDBParser, MMCIFParser
from .cache import disk_cache
from .uniprot import create_session

# 创建统一的requests.Session对象
_session = create_session()

# AlphaFold数据库API URL
AFDB_API_URL = "https://alphafold.ebi.ac.uk/api/prediction/{}"

class AlphaFoldData:
    """AlphaFold数据类"""
    def __init__(self, uniprot_id, plddt_scores):
        self.uniprot_id = uniprot_id
        self.plddt_scores = plddt_scores  # list of (position, score) tuples
    
    def get_plddt_at_position(self, position):
        """获取特定位置的pLDDT分数
        
        Args:
            position: 1-based 位置
            
        Returns:
            float: pLDDT分数，如果位置不存在则返回None
        """
        for pos, score in self.plddt_scores:
            if pos == position:
                return score
        return None

@disk_cache(duration=timedelta(days=30))
def fetch_afdb_predictions(uniprot_id):
    """从AlphaFold数据库API获取预测数据
    
    Args:
        uniprot_id: UniProt ID字符串
        
    Returns:
        list[dict]: 包含预测信息的字典列表，如果API请求失败则返回空列表
    
    Raises:
        requests.exceptions.HTTPError: 如果API请求失败（除了404错误）
    """
    url = AFDB_API_URL.format(uniprot_id)
    
    try:
        response = _session.get(url, timeout=(5, 60))
        response.raise_for_status()
        data = response.json()
        # 如果返回空对象或空列表，返回None而不是空列表，避免被缓存
        if not data:
            return None
        return data
    except requests.exceptions.HTTPError as e:
        # 如果是404错误，返回None而不是空列表
        if e.response.status_code == 404:
            return None
        # 其他HTTP错误直接抛出原始异常
        raise
    except requests.exceptions.RequestException as e:
        raise

@disk_cache(duration=timedelta(days=30), cache_none=False)
def get_alphafold_data(uniprot_id):
    """获取AlphaFold数据
    
    Args:
        uniprot_id: UniProt ID字符串
        
    Returns:
        AlphaFoldData 对象，如果AlphaFold数据不存在则返回None
    
    Raises:
        requests.exceptions.HTTPError: 如果下载失败（除了404错误）
    """
    # 从AFDB API获取预测数据
    predictions = fetch_afdb_predictions(uniprot_id)
    
    if not predictions:
        return None
    
    # 找到最匹配的预测条目
    target_entry_id = f"AF-{uniprot_id}-F1"
    selected_prediction = None
    
    # 优先选择entryId匹配的条目
    for pred in predictions:
        if pred.get("entryId") == target_entry_id:
            selected_prediction = pred
            break
    
    # 如果没有找到entryId匹配的，尝试匹配modelEntityId
    if not selected_prediction:
        for pred in predictions:
            if pred.get("modelEntityId") == uniprot_id:
                selected_prediction = pred
                break
    
    # 如果还是没有找到，使用第一个条目
    if not selected_prediction:
        selected_prediction = predictions[0]
    
    # 获取PDB URL，如果没有则尝试CIF URL
    pdb_url = selected_prediction.get("pdbUrl")
    if not pdb_url:
        pdb_url = selected_prediction.get("cifUrl")
        if not pdb_url:
            return None
    
    # 下载结构内容
    try:
        response = _session.get(pdb_url, timeout=(5, 60))
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # 如果是404错误，返回None
        if e.response.status_code == 404:
            return None
        # 其他HTTP错误直接抛出原始异常
        raise
    except requests.exceptions.RequestException as e:
        raise
    
    # 检查文件是否为gzip格式并解压缩
    if pdb_url.endswith(".gz"):
        structure_content = gzip.decompress(response.content).decode('utf-8')
    else:
        structure_content = response.content.decode('utf-8')
    
    # 解析结构文件
    plddt_scores = []
    
    from io import StringIO
    
    # 根据文件格式选择解析器
    if pdb_url.lower().endswith('.cif') or pdb_url.lower().endswith('.mmcif') or pdb_url.lower().endswith('.cif.gz') or pdb_url.lower().endswith('.mmcif.gz'):
        parser = MMCIFParser(QUIET=True)
    else:
        parser = PDBParser(QUIET=True)
    
    structure = parser.get_structure(uniprot_id, StringIO(structure_content))
    
    # 遍历所有原子，提取B-factor作为pLDDT分数
    seen_positions = set()
    
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] != ' ':
                    continue  # 跳过非标准残基
                
                position = residue.id[1]
                if position in seen_positions:
                    continue
                seen_positions.add(position)
                
                # 获取第一个原子的B-factor（通常所有原子相同）
                for atom in residue:
                    plddt = atom.get_bfactor()
                    plddt_scores.append((position, plddt))
                    break
    
    # 按位置排序
    plddt_scores.sort(key=lambda x: x[0])
    
    return AlphaFoldData(uniprot_id, plddt_scores)

def download_pdb(uniprot_id, save_dir=None):
    """下载AlphaFold PDB文件
    
    Args:
        uniprot_id: UniProt ID字符串
        save_dir: 保存目录，默认使用系统临时目录
        
    Returns:
        str: PDB文件路径
    """
    if save_dir is None:
        save_dir = tempfile.gettempdir()
    
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    # 检查本地文件是否存在（首先尝试本地fallback）
    # 1. 检查环境变量ALPHAFOLD_LOCAL_DIR
    local_dir = os.environ.get("ALPHAFOLD_LOCAL_DIR")
    if local_dir is None:
        # 2. 检查当前目录下的models子目录
        local_dir = os.path.join(os.getcwd(), "models")
    
    # 尝试找到本地结构文件
    target_entry_id = f"AF-{uniprot_id}-F1"
    local_filenames = [
        f"{target_entry_id}-model_v6.pdb",
        f"{target_entry_id}-model_v6.cif",
        f"{target_entry_id}-model_v6.pdb.gz",
        f"{target_entry_id}-model_v6.cif.gz"
    ]
    
    # 检查本地文件
    for filename in local_filenames:
        local_file_path = os.path.join(local_dir, filename)
        if os.path.exists(local_file_path):
            # 如果是压缩文件，解压到临时目录
            if filename.endswith(".gz"):
                import gzip
                output_filename = filename[:-3]
                output_path = os.path.join(save_dir, output_filename)
                
                with gzip.open(local_file_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                return output_path
            return local_file_path
    
    # 如果没有本地文件，继续从API获取
    # 从AFDB API获取预测数据
    predictions = fetch_afdb_predictions(uniprot_id)
    
    if not predictions:
        return None
    
    # 找到最匹配的预测条目
    selected_prediction = None
    
    # 优先选择entryId匹配的条目
    for pred in predictions:
        if pred.get("entryId") == target_entry_id:
            selected_prediction = pred
            break
    
    # 如果没有找到entryId匹配的，尝试匹配modelEntityId
    if not selected_prediction:
        for pred in predictions:
            if pred.get("modelEntityId") == uniprot_id:
                selected_prediction = pred
                break
    
    # 如果还是没有找到，使用第一个条目
    if not selected_prediction:
        selected_prediction = predictions[0]
    
    # 获取PDB URL
    pdb_url = selected_prediction.get("pdbUrl")
    if not pdb_url:
        pdb_url = selected_prediction.get("cifUrl")
        if not pdb_url:
            raise Exception(f"No PDB or CIF URL found for UniProt ID {uniprot_id}")
    
    # 从URL获取文件名
    pdb_filename = os.path.basename(pdb_url)
    # 如果是压缩文件，去掉.gz后缀
    if pdb_filename.endswith(".gz"):
        pdb_filename = pdb_filename[:-3]
    
    pdb_file = os.path.join(save_dir, pdb_filename)
    
    # 如果文件已存在，直接返回
    if os.path.exists(pdb_file):
        return pdb_file
    
    tmp_gz_path = None
    tmp_pdb_path = None
    
    try:
        response = _session.get(pdb_url, stream=True, timeout=(5, 60))
        response.raise_for_status()
        
        # 检查文件是否为压缩格式
        is_gzipped = pdb_url.endswith(".gz")
        
        if is_gzipped:
            # 使用临时文件进行下载和解压缩，确保原子操作
            with tempfile.NamedTemporaryFile(dir=save_dir, suffix=".pdb.gz", delete=False, mode='wb') as tmp_gz_file:
                tmp_gz_path = tmp_gz_file.name
                # 写入压缩数据
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_gz_file.write(chunk)
            
            # 解压缩到临时PDB文件
            with tempfile.NamedTemporaryFile(dir=save_dir, suffix=".pdb", delete=False, mode='wb') as tmp_pdb_file:
                tmp_pdb_path = tmp_pdb_file.name
                with gzip.open(tmp_gz_path, 'rb') as f_in:
                    tmp_pdb_file.write(f_in.read())
        else:
            # 直接下载未压缩的PDB文件
            with tempfile.NamedTemporaryFile(dir=save_dir, suffix=".pdb", delete=False, mode='wb') as tmp_pdb_file:
                tmp_pdb_path = tmp_pdb_file.name
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_pdb_file.write(chunk)
        
        # 原子重命名到最终位置
        os.replace(tmp_pdb_path, pdb_file)
        
        # 清理临时压缩文件
        if tmp_gz_path and os.path.exists(tmp_gz_path):
            os.remove(tmp_gz_path)
            
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(f"Failed to download AlphaFold PDB for ID {uniprot_id}: HTTP {response.status_code} - {response.reason}")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Network error when downloading AlphaFold PDB for ID {uniprot_id}: {str(e)}")
    except Exception as e:
        # 清理临时文件
        if tmp_gz_path and os.path.exists(tmp_gz_path):
            os.remove(tmp_gz_path)
        if tmp_pdb_path and os.path.exists(tmp_pdb_path):
            os.remove(tmp_pdb_path)
        raise Exception(f"Error downloading or processing AlphaFold PDB for ID {uniprot_id}: {str(e)}")
    
    return pdb_file
