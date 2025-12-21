import os
import requests
import gzip
from datetime import timedelta
from Bio.PDB import PDBParser
from .cache import disk_cache

# AlphaFold数据库URL
ALPHAFOLD_URL = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v4.pdb.gz"

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
        AlphaFoldData 对象
    
    Raises:
        requests.exceptions.HTTPError: 如果下载失败
    """
    # 下载PDB文件
    pdb_gz_url = ALPHAFOLD_URL.format(uniprot_id)
    response = requests.get(pdb_gz_url)
    response.raise_for_status()
    
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
    
    pdb_file = os.path.join(save_dir, f"AF-{uniprot_id}-F1-model_v4.pdb")
    
    # 如果文件已存在，直接返回
    if os.path.exists(pdb_file):
        return pdb_file
    
    # 下载并解压缩
    pdb_gz_url = ALPHAFOLD_URL.format(uniprot_id)
    response = requests.get(pdb_gz_url)
    response.raise_for_status()
    
    with gzip.open(response.raw, 'rt') as f_in:
        with open(pdb_file, 'w') as f_out:
            f_out.write(f_in.read())
    
    return pdb_file
