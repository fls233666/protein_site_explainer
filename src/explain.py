import pandas as pd
from .parsing import parse_mutation_list, validate_mutations, mutations_to_df
from .uniprot import get_uniprot_entry, map_features_to_mutations, format_features_for_display
from .alphafold import get_alphafold_data
from .esm_scoring import score_mutations
from .cache import disk_cache
from datetime import timedelta

class Explainer:
    """蛋白质位点解释器"""
    
    @disk_cache(duration=timedelta(days=7))
    def explain(self, uniprot_id, mutation_list_str, calculate_sensitivity=True):
        """解释蛋白质突变
        
        Args:
            uniprot_id: UniProt ID字符串
            mutation_list_str: 突变列表字符串，如 "A123T, K456M"
            calculate_sensitivity: 是否计算位点敏感度
            
        Returns:
            dict: 包含所有解释结果的数据结构
        """
        # 1. 获取UniProt数据
        uniprot_entry = get_uniprot_entry(uniprot_id)
        sequence = uniprot_entry.sequence
        
        # 2. 解析突变列表
        mutations = parse_mutation_list(mutation_list_str)
        
        # 3. 验证突变
        validate_mutations(mutations, sequence)
        
        # 4. 计算ESM评分
        esm_results = score_mutations(sequence, mutations, calculate_sensitivity)
        
        # 5. 获取AlphaFold数据（可能返回None）
        alphafold_data = get_alphafold_data(uniprot_id)
        
        # 6. 映射UniProt特征到突变位置
        feature_map = map_features_to_mutations(mutations, uniprot_entry.features)
        
        # 7. 构建结果数据框
        results = []
        
        for mutation, esm_result in zip(mutations, esm_results):
            position = mutation.position
            
            # 获取pLDDT分数（处理AlphaFold数据不存在的情况）
            plddt = None
            if alphafold_data is not None:
                plddt = alphafold_data.get_plddt_at_position(position)
            
            # 获取特征
            features = feature_map.get(position, [])
            features_str = format_features_for_display(features)
            
            results.append({
                "Mutation": str(mutation),
                "Wildtype": mutation.wt_aa,
                "Position": position,
                "Mutant": mutation.mut_aa,
                "ESM_LLR": esm_result["llr"],
                "Site_Sensitivity": esm_result["sensitivity"],
                "AlphaFold_pLDDT": plddt,
                "UniProt_Features": features_str
            })
        
        df_results = pd.DataFrame(results)
        
        # 8. 构建完整结果
        full_result = {
            "uniprot_id": uniprot_id,
            "sequence": sequence,
            "mutations": mutations,
            "results_df": df_results,
            "uniprot_entry": uniprot_entry,
            "alphafold_data": alphafold_data
        }
        
        return full_result
    
    def to_csv(self, result, output_file):
        """将结果保存为CSV文件
        
        Args:
            result: explain方法返回的结果字典
            output_file: 输出CSV文件路径
        """
        result["results_df"].to_csv(output_file, index=False)
    
    def get_sequence_with_mutations(self, sequence, mutations):
        """获取带有突变标记的序列
        
        Args:
            sequence: 原始蛋白质序列
            mutations: Mutation 对象列表
            
        Returns:
            str: 带有突变标记的序列
        
        Warning:
            此方法已弃用，不再用于UI渲染。请使用src/sequence_view模块中的功能。
        """
        import warnings
        warnings.warn(
            "get_sequence_with_mutations() is deprecated and no longer used for UI rendering. "
            "Please use functions from src/sequence_view module.",
            DeprecationWarning,
            stacklevel=2
        )
        
        seq_list = list(sequence)
        mutation_positions = set(mutation.position for mutation in mutations)
        
        # 在突变位置添加标记
        result = []
        for i, aa in enumerate(seq_list):
            position = i + 1
            if position in mutation_positions:
                result.append(f"[{aa}]")
            else:
                result.append(aa)
        
        return "".join(result)
    
    def get_plddt_profile(self, alphafold_data):
        """获取pLDDT分布曲线数据
        
        Args:
            alphafold_data: AlphaFoldData 对象，可能为None
            
        Returns:
            pandas.DataFrame: 包含位置和pLDDT分数的数据框，如果没有AlphaFold数据则返回None
        """
        if alphafold_data is None or not alphafold_data.plddt_scores:
            return None
        
        positions, scores = zip(*alphafold_data.plddt_scores)
        return pd.DataFrame({"Position": positions, "pLDDT": scores})

# 创建全局解释器实例
explainer = Explainer()

def explain_mutations(uniprot_id, mutation_list_str, calculate_sensitivity=True):
    """解释突变的便捷函数
    
    Args:
        uniprot_id: UniProt ID字符串
        mutation_list_str: 突变列表字符串
        calculate_sensitivity: 是否计算位点敏感度
        
    Returns:
        dict: 解释结果
    """
    return explainer.explain(uniprot_id, mutation_list_str, calculate_sensitivity)

def generate_csv(result, output_file):
    """生成CSV文件的便捷函数
    
    Args:
        result: 解释结果
        output_file: 输出文件路径
    """
    explainer.to_csv(result, output_file)
