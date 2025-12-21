import re
import pandas as pd

# 突变格式正则表达式（A123T）
MUTATION_PATTERN = re.compile(r'^([A-Z])(\d+)([A-Z*])$')

class Mutation:
    """突变数据类"""
    def __init__(self, wt_aa, position, mut_aa):
        self.wt_aa = wt_aa
        self.position = position  # 1-based
        self.mut_aa = mut_aa
    
    def __str__(self):
        return f"{self.wt_aa}{self.position}{self.mut_aa}"
    
    def __repr__(self):
        return f"Mutation(wt_aa='{self.wt_aa}', position={self.position}, mut_aa='{self.mut_aa}')"

def parse_mutation(mutation_str):
    """解析单个突变字符串
    
    Args:
        mutation_str: 突变字符串，如 "A123T"
    
    Returns:
        Mutation 对象
    
    Raises:
        ValueError: 如果突变格式无效
    """
    match = MUTATION_PATTERN.match(mutation_str.strip())
    if not match:
        raise ValueError(f"Invalid mutation format: {mutation_str}")
    
    wt_aa = match.group(1)
    position = int(match.group(2))
    mut_aa = match.group(3)
    
    return Mutation(wt_aa, position, mut_aa)

def parse_mutation_list(mutation_list_str):
    """解析突变列表字符串
    
    Args:
        mutation_list_str: 逗号或空格分隔的突变列表，如 "A123T, K456M, R789L"
    
    Returns:
        list of Mutation 对象
    """
    # 支持逗号或空格分隔
    mutation_strs = re.split(r'[,\s]+', mutation_list_str.strip())
    mutations = []
    
    for mutation_str in mutation_strs:
        if mutation_str:
            try:
                mutations.append(parse_mutation(mutation_str))
            except ValueError:
                raise ValueError(f"Invalid mutation in list: {mutation_str}")
    
    return mutations

def validate_mutations(mutations, protein_sequence):
    """验证突变是否与蛋白质序列一致
    
    Args:
        mutations: Mutation 对象列表
        protein_sequence: 蛋白质序列字符串
    
    Raises:
        ValueError: 如果突变的野生型氨基酸与序列不符
    """
    for mutation in mutations:
        if mutation.position < 1 or mutation.position > len(protein_sequence):
            raise ValueError(f"Mutation position {mutation.position} out of bounds for sequence of length {len(protein_sequence)}")
        
        actual_wt = protein_sequence[mutation.position - 1]  # 0-based index
        if actual_wt != mutation.wt_aa:
            raise ValueError(f"Mutation {mutation} wildtype mismatch: expected {mutation.wt_aa}, got {actual_wt}")

def mutations_to_df(mutations):
    """将突变列表转换为DataFrame
    
    Args:
        mutations: Mutation 对象列表
    
    Returns:
        pandas.DataFrame: 包含突变信息的DataFrame
    """
    data = {
        "Mutation": [str(mut) for mut in mutations],
        "Wildtype": [mut.wt_aa for mut in mutations],
        "Position": [mut.position for mut in mutations],
        "Mutant": [mut.mut_aa for mut in mutations]
    }
    
    return pd.DataFrame(data)

def df_to_mutations(df):
    """将DataFrame转换为突变列表
    
    Args:
        df: 包含突变信息的DataFrame
    
    Returns:
        list of Mutation 对象
    """
    mutations = []
    for _, row in df.iterrows():
        if "Mutation" in row:
            mutations.append(parse_mutation(row["Mutation"]))
        else:
            mutations.append(Mutation(row["Wildtype"], row["Position"], row["Mutant"]))
    
    return mutations
