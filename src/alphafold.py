import os
import requests
import gzip
import tempfile
from datetime import timedelta
from Bio.PDB import PDBParser
from .cache import disk_cache
from .uniprot import create_session

# AlphaFold数据库URL
ALPHAFOLD_URL = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v4.pdb.gz"

# 创建统一的requests.Session对象
_session = create_session()

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
def get_alphafold_data(uniprot_id):
    """获取AlphaFold数据
    
    Args:
        uniprot_id: UniProt ID字符串
        
    Returns:
        AlphaFoldData 对象，如果AlphaFold数据不存在则返回None
    
    Raises:
        requests.exceptions.HTTPError: 如果下载失败（除了404错误）
    """
    # 下载PDB文件
    pdb_gz_url = ALPHAFOLD_URL.format(uniprot_id)
    
    try:
        response = _session.get(pdb_gz_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # 如果是404错误，返回None
        if response.status_code == 404:
            return None
        # 其他HTTP错误仍然抛出异常
        raise requests.exceptions.HTTPError(f"Failed to fetch AlphaFold data for ID {uniprot_id}: HTTP {response.status_code} - {response.reason}")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Network error when fetching AlphaFold data for ID {uniprot_id}: {str(e)}")
    
    # 解压缩PDB内容
    pdb_content = gzip.decompress(response.content).decode('utf-8')
    
    # 解析PDB文件
    plddt_scores = []
    
    # 使用Bio.PDB解析
    from io import StringIO
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(uniprot_id, StringIO(pdb_content))
    
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
        save_dir: 保存目录，默认使用当前目录
        
    Returns:
        str: PDB文件路径
    """
    if save_dir is None:
        save_dir = os.getcwd()
    
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    pdb_file = os.path.join(save_dir, f"AF-{uniprot_id}-F1-model_v4.pdb")
    
    # 如果文件已存在，直接返回
    if os.path.exists(pdb_file):
        return pdb_file
    
    # 下载并解压缩
    pdb_gz_url = ALPHAFOLD_URL.format(uniprot_id)
    
    try:
        response = _session.get(pdb_gz_url, stream=True)
        response.raise_for_status()
        
        # 使用临时文件进行下载和解压缩，确保原子操作
        with tempfile.NamedTemporaryFile(dir=save_dir, suffix=".pdb.gz", delete=False) as tmp_gz_file:
            tmp_gz_path = tmp_gz_file.name
            # 写入压缩数据
            for chunk in response.iter_content(chunk_size=8192):
                tmp_gz_file.write(chunk)
        
        # 解压缩到临时PDB文件
        with tempfile.NamedTemporaryFile(dir=save_dir, suffix=".pdb", delete=False) as tmp_pdb_file:
            tmp_pdb_path = tmp_pdb_file.name
            with gzip.open(tmp_gz_path, 'rt') as f_in:
                tmp_pdb_file.write(f_in.read())
        
        # 原子重命名到最终位置
        os.replace(tmp_pdb_path, pdb_file)
        
        # 清理临时压缩文件
        os.remove(tmp_gz_path)
        
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(f"Failed to download AlphaFold PDB for ID {uniprot_id}: HTTP {response.status_code} - {response.reason}")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Network error when downloading AlphaFold PDB for ID {uniprot_id}: {str(e)}")
    except Exception as e:
        # 清理临时文件
        for tmp_path in [tmp_gz_path, tmp_pdb_path]:
            if 'tmp_gz_path' in locals() and os.path.exists(tmp_gz_path):
                os.remove(tmp_gz_path)
            if 'tmp_pdb_path' in locals() and os.path.exists(tmp_pdb_path):
                os.remove(tmp_pdb_path)
        raise Exception(f"Error downloading or processing AlphaFold PDB for ID {uniprot_id}: {str(e)}")
    
    return pdb_file
