import torch
import esm
import numpy as np
from .cache import disk_cache
from datetime import timedelta

# 氨基酸字母表（ESM模型使用的顺序）
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
AA_TO_INDEX = {aa: i for i, aa in enumerate(AMINO_ACIDS)}

class ESMScorer:
    """ESM评分器类"""
    def __init__(self, model_name="esm2_t6_8M_UR50D"):
        self.model_name = model_name
        self.model = None
        self.alphabet = None
        self.batch_converter = None
        self.load_model()
    
    def load_model(self):
        """加载ESM模型"""
        if self.model is None:
            # 加载预训练模型
            model_func = getattr(esm.pretrained, self.model_name)
            self.model, self.alphabet = model_func()
            self.model.eval()
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            self.batch_converter = self.alphabet.get_batch_converter()
    
    @torch.no_grad()
    def get_logits(self, sequence):
        """获取序列的logits
        
        Args:
            sequence: 蛋白质序列字符串
            
        Returns:
            numpy array: 形状为 (sequence_length, num_amino_acids) 的logits矩阵
        """
        # 准备输入
        data = [("protein", sequence)]
        batch_labels, batch_strs, batch_tokens = self.batch_converter(data)
        
        if torch.cuda.is_available():
            batch_tokens = batch_tokens.cuda()
        
        # 前向传播
        results = self.model(batch_tokens, repr_layers=[], return_logits=True)
        logits = results["logits"].cpu().numpy()
        
        # 移除起始和结束标记
        return logits[0, 1:-1, :]  # (seq_len, 21)
    
    def calculate_llr(self, sequence, position, wt_aa, mut_aa):
        """计算单个突变的LLR
        
        Args:
            sequence: 完整的蛋白质序列
            position: 1-based 突变位置
            wt_aa: 野生型氨基酸
            mut_aa: 突变型氨基酸
            
        Returns:
            float: LLR值 (logP(mut) - logP(wt))
        """
        # 创建mask序列
        mask_sequence = list(sequence)
        mask_sequence[position - 1] = self.alphabet.get_tok(self.alphabet.mask_idx)
        mask_sequence = "".join(mask_sequence)
        
        # 获取logits
        logits = self.get_logits(mask_sequence)
        target_logits = logits[position - 1, :]
        
        # 转换为概率
        probs = torch.softmax(torch.tensor(target_logits), dim=0).numpy()
        
        # 计算LLR
        wt_idx = AA_TO_INDEX[wt_aa]
        mut_idx = AA_TO_INDEX[mut_aa]
        
        llr = np.log(probs[mut_idx] + 1e-10) - np.log(probs[wt_idx] + 1e-10)
        
        return llr
    
    def calculate_sensitivity(self, sequence, position, wt_aa, full_length=False):
        """计算位点敏感度
        
        Args:
            sequence: 完整的蛋白质序列
            position: 1-based 位置
            wt_aa: 野生型氨基酸
            full_length: 是否计算全长序列的敏感度，默认为False（只计算突变位置）
            
        Returns:
            float: 敏感度值 (mean_{aa!=wt}(logP(aa) - logP(wt)))
        """
        if full_length:
            raise NotImplementedError("Full length sensitivity calculation not implemented yet")
        
        # 创建mask序列
        mask_sequence = list(sequence)
        mask_sequence[position - 1] = self.alphabet.mask_idx
        mask_sequence = "".join(mask_sequence)
        
        # 获取logits
        logits = self.get_logits(mask_sequence)
        target_logits = logits[position - 1, :]
        
        # 转换为概率
        probs = torch.softmax(torch.tensor(target_logits), dim=0).numpy()
        
        # 计算敏感度
        wt_idx = AA_TO_INDEX[wt_aa]
        wt_prob = probs[wt_idx]
        
        llr_sum = 0.0
        count = 0
        
        for aa, idx in AA_TO_INDEX.items():
            if aa != wt_aa:
                aa_prob = probs[idx]
                llr_sum += np.log(aa_prob + 1e-10) - np.log(wt_prob + 1e-10)
                count += 1
        
        sensitivity = llr_sum / count
        
        return sensitivity
    
    def score_mutations(self, sequence, mutations, calculate_sensitivity=True):
        """批量计算突变的LLR和敏感度
        
        Args:
            sequence: 完整的蛋白质序列
            mutations: Mutation 对象列表
            calculate_sensitivity: 是否计算敏感度
            
        Returns:
            list of dict: 每个突变的评分结果
        """
        results = []
        
        for mutation in mutations:
            # 验证突变
            if mutation.wt_aa != sequence[mutation.position - 1]:
                raise ValueError(f"Mutation {mutation} wildtype mismatch")
            
            # 计算LLR
            llr = self.calculate_llr(
                sequence=sequence,
                position=mutation.position,
                wt_aa=mutation.wt_aa,
                mut_aa=mutation.mut_aa
            )
            
            # 计算敏感度
            sensitivity = None
            if calculate_sensitivity:
                sensitivity = self.calculate_sensitivity(
                    sequence=sequence,
                    position=mutation.position,
                    wt_aa=mutation.wt_aa,
                    full_length=False
                )
            
            results.append({
                "mutation": str(mutation),
                "position": mutation.position,
                "wt_aa": mutation.wt_aa,
                "mut_aa": mutation.mut_aa,
                "llr": llr,
                "sensitivity": sensitivity
            })
        
        return results

# 创建全局ESM评分器实例
esm_scorer = ESMScorer()

@disk_cache(duration=timedelta(days=7))
def score_mutations(sequence, mutations, calculate_sensitivity=True):
    """缓存包装的突变评分函数
    
    Args:
        sequence: 完整的蛋白质序列
        mutations: Mutation 对象列表
        calculate_sensitivity: 是否计算敏感度
        
    Returns:
        list of dict: 每个突变的评分结果
    """
    return esm_scorer.score_mutations(sequence, mutations, calculate_sensitivity)
