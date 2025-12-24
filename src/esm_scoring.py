import numpy as np
from .cache import disk_cache
from datetime import timedelta
import streamlit as st

# 标准氨基酸字母表
STANDARD_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

class ESMScorer:
    """ESM评分器类"""
    def __init__(self, model_name="esm2_t6_8M_UR50D", device=None):
        self.model_name = model_name
        self.model = None
        self.alphabet = None
        self.batch_converter = None
        self.device = device
    
    def load_model(self):
        """加载ESM模型"""
        if self.model is None:
            # 延迟导入torch和esm
            import torch
            import esm
            
            # 初始化设备
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                
            # 加载预训练模型
            # 兼容ESM 3.x、2.x和旧版本的API
            try:
                # 首先尝试直接使用esm.pretrained.load_model_and_alphabet（这是ESM 3.x的标准API）
                self.model, self.alphabet = esm.pretrained.load_model_and_alphabet(self.model_name)
            except Exception as e1:
                try:
                    # ESM 2.x API：从esm.model_zoo导入
                    if hasattr(esm, 'model_zoo'):
                        from esm.model_zoo import get_pretrained_model
                        self.model, self.alphabet = get_pretrained_model(self.model_name)
                    else:
                        raise ValueError(f"Could not load model '{self.model_name}'. ESM version not compatible.")
                except Exception as e2:
                    try:
                        # 旧API：从esm.pretrained导入get_pretrained_model
                        if hasattr(esm.pretrained, 'get_pretrained_model'):
                            from esm.pretrained import get_pretrained_model
                            self.model, self.alphabet = get_pretrained_model(self.model_name)
                        else:
                            raise ValueError(f"Could not load model '{self.model_name}'. ESM version not compatible.")
                    except Exception as e3:
                        try:
                            # 最旧API：直接访问esm.pretrained中的模型函数
                            if hasattr(esm.pretrained, self.model_name):
                                model_func = getattr(esm.pretrained, self.model_name)
                                self.model, self.alphabet = model_func()
                            else:
                                raise ValueError(f"Could not load model '{self.model_name}'. Model name not found in esm.pretrained.")
                        except Exception as e4:
                            raise ValueError(
                                f"Could not load model '{self.model_name}' with any API. "
                                f"ESM version: {esm.__version__}\n"  # 添加ESM版本信息
                                f"API attempts failed with errors:\n"  # 添加详细错误信息
                                f"1. load_model_and_alphabet: {e1}\n"  # 第一个API尝试的错误
                                f"2. model_zoo.get_pretrained_model: {e2}\n"  # 第二个API尝试的错误
                                f"3. pretrained.get_pretrained_model: {e3}\n"  # 第三个API尝试的错误
                                f"4. direct model function call: {e4}\n"  # 第四个API尝试的错误
                            )
            self.model.eval()
            try:
                self.model = self.model.to(self.device)
            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"CUDA out of memory, falling back to CPU")
                    self.device = "cpu"
                    self.model = self.model.to(self.device)
                else:
                    raise e
            self.batch_converter = self.alphabet.get_batch_converter()
    
    def get_logits(self, sequence):
        """获取序列的logits
        
        Args:
            sequence: 蛋白质序列字符串，允许包含<mask>标记
            
        Returns:
            numpy array: 形状为 (sequence_length, num_tokens) 的logits矩阵
        """
        # 确保模型已加载
        self.load_model()
        
        # 验证序列（允许<mask>标记）
        if '<mask>' in sequence:
            # 分割并验证每个部分
            parts = sequence.split('<mask>')
            for part in parts:
                for aa in part:
                    if aa not in STANDARD_AMINO_ACIDS:
                        raise ValueError(f"Non-standard amino acid '{aa}' found in sequence")
        else:
            # 没有<mask>，验证整个序列
            for aa in sequence:
                if aa not in STANDARD_AMINO_ACIDS:
                    raise ValueError(f"Non-standard amino acid '{aa}' found in sequence")
        
        # 准备输入
        data = [("protein", sequence)]
        batch_labels, batch_strs, batch_tokens = self.batch_converter(data)
        
        try:
            # 延迟导入torch以使用no_grad上下文管理器
            import torch
            
            with torch.no_grad():
                batch_tokens = batch_tokens.to(self.device)
                # 前向传播
                results = self.model(batch_tokens, repr_layers=[])
                logits = results["logits"].detach().cpu().numpy()
        except RuntimeError as e:
            if "out of memory" in str(e):
                print(f"CUDA out of memory during inference, falling back to CPU")
                self.device = "cpu"
                self.model = self.model.to(self.device)
                
                with torch.no_grad():
                    batch_tokens = batch_tokens.to(self.device)
                    results = self.model(batch_tokens, repr_layers=[])
                    logits = results["logits"].detach().cpu().numpy()
            else:
                raise e
        
        # 移除起始和结束标记
        return logits[0, 1:-1, :]  # (seq_len, num_tokens)
    
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
        # 确保模型已加载
        self.load_model()
        
        # 验证氨基酸
        if wt_aa not in STANDARD_AMINO_ACIDS:
            raise ValueError(f"Wildtype amino acid '{wt_aa}' is not a standard amino acid")
        if mut_aa not in STANDARD_AMINO_ACIDS:
            raise ValueError(f"Mutant amino acid '{mut_aa}' is not a standard amino acid")
        
        # 验证序列位置
        if position < 1 or position > len(sequence):
            raise ValueError(f"Position {position} is out of sequence bounds (1-{len(sequence)})")
        if sequence[position - 1] != wt_aa:
            raise ValueError(f"Sequence at position {position} is '{sequence[position - 1]}', expected wildtype '{wt_aa}'")
        
        # 创建mask序列
        mask_sequence = list(sequence)
        mask_sequence[position - 1] = self.alphabet.get_tok(self.alphabet.mask_idx)
        mask_sequence = "".join(mask_sequence)
        
        # 获取logits
        logits = self.get_logits(mask_sequence)
        target_logits = logits[position - 1, :]
        
        # 转换为概率 (使用PyTorch避免numpy<->torch拷贝)
        import torch
        
        with torch.no_grad():
            probs_tensor = torch.softmax(torch.tensor(target_logits).to(self.device), dim=0)
            
            # 计算LLR，使用ESM alphabet的真实token索引
            wt_idx = self.alphabet.tok_to_idx[wt_aa]
            mut_idx = self.alphabet.tok_to_idx[mut_aa]
            
            llr = (torch.log(probs_tensor[mut_idx] + 1e-10) - torch.log(probs_tensor[wt_idx] + 1e-10)).cpu().item()
        
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
        # 确保模型已加载
        self.load_model()
        
        if full_length:
            raise NotImplementedError("Full length sensitivity calculation not implemented yet")
        
        # 验证氨基酸
        if wt_aa not in STANDARD_AMINO_ACIDS:
            raise ValueError(f"Wildtype amino acid '{wt_aa}' is not a standard amino acid")
        
        # 验证序列位置
        if position < 1 or position > len(sequence):
            raise ValueError(f"Position {position} is out of sequence bounds (1-{len(sequence)})")
        if sequence[position - 1] != wt_aa:
            raise ValueError(f"Sequence at position {position} is '{sequence[position - 1]}', expected wildtype '{wt_aa}'")
        
        # 创建mask序列
        mask_sequence = list(sequence)
        mask_sequence[position - 1] = self.alphabet.get_tok(self.alphabet.mask_idx)
        mask_sequence = "".join(mask_sequence)
        
        # 获取logits
        logits = self.get_logits(mask_sequence)
        target_logits = logits[position - 1, :]
        
        # 转换为概率 (使用PyTorch避免numpy<->torch拷贝)
        import torch
        
        with torch.no_grad():
            probs_tensor = torch.softmax(torch.tensor(target_logits).to(self.device), dim=0)
            
            # 计算敏感度，只针对标准氨基酸
            wt_idx = self.alphabet.tok_to_idx[wt_aa]
            wt_prob = probs_tensor[wt_idx]
            
            # 矢量化计算所有标准氨基酸的LLR
            llr_values = []
            for aa in STANDARD_AMINO_ACIDS:
                if aa != wt_aa:
                    aa_idx = self.alphabet.tok_to_idx[aa]
                    aa_prob = probs_tensor[aa_idx]
                    llr_values.append(torch.log(aa_prob + 1e-10) - torch.log(wt_prob + 1e-10))
            
            if llr_values:
                sensitivity = torch.mean(torch.stack(llr_values)).cpu().item()
            else:
                sensitivity = 0.0
        
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
        # 确保模型已加载
        self.load_model()
        
        # 验证所有突变的氨基酸和位置
        for mutation in mutations:
            if mutation.wt_aa not in STANDARD_AMINO_ACIDS:
                raise ValueError(f"Wildtype amino acid '{mutation.wt_aa}' is not a standard amino acid")
            if mutation.mut_aa not in STANDARD_AMINO_ACIDS:
                raise ValueError(f"Mutant amino acid '{mutation.mut_aa}' is not a standard amino acid")
            if mutation.position < 1 or mutation.position > len(sequence):
                raise ValueError(f"Position {mutation.position} is out of sequence bounds (1-{len(sequence)})")
            if sequence[mutation.position - 1] != mutation.wt_aa:
                raise ValueError(f"Mutation {mutation} wildtype mismatch: expected {sequence[mutation.position - 1]}, got {mutation.wt_aa}")
        
        results = []
        
        # 对于每个突变位置，批量计算所有需要的突变
        position_groups = {}
        for mutation in mutations:
            if mutation.position not in position_groups:
                position_groups[mutation.position] = []
            position_groups[mutation.position].append(mutation)
        
        # 延迟导入torch
        import torch
        
        for position, group_mutations in position_groups.items():
            # 创建mask序列
            mask_sequence = list(sequence)
            mask_sequence[position - 1] = self.alphabet.get_tok(self.alphabet.mask_idx)
            mask_sequence = "".join(mask_sequence)
            
            # 获取logits
            logits = self.get_logits(mask_sequence)
            target_logits = logits[position - 1, :]
            
            with torch.no_grad():
                # 转换为概率 (直接在设备上使用PyTorch，避免numpy<->torch拷贝)
                probs_tensor = torch.softmax(torch.tensor(target_logits).to(self.device), dim=0)
                
                # 计算该位置所有突变的LLR
                wt_aa = group_mutations[0].wt_aa  # 同一位置的野生型氨基酸相同
                wt_idx = self.alphabet.tok_to_idx[wt_aa]
                wt_prob = probs_tensor[wt_idx]
                
                # 计算敏感度（如果需要）
                sensitivity = None
                if calculate_sensitivity:
                    # 矢量化计算所有标准氨基酸的LLR
                    llr_values = []
                    for aa in STANDARD_AMINO_ACIDS:
                        if aa != wt_aa:
                            aa_idx = self.alphabet.tok_to_idx[aa]
                            aa_prob = probs_tensor[aa_idx]
                            llr_values.append(torch.log(aa_prob + 1e-10) - torch.log(wt_prob + 1e-10))
                    
                    if llr_values:
                        sensitivity = torch.mean(torch.stack(llr_values)).cpu().item()
                
                # 为该位置的每个突变计算LLR
                for mutation in group_mutations:
                    mut_idx = self.alphabet.tok_to_idx[mutation.mut_aa]
                    mut_prob = probs_tensor[mut_idx]
                    llr = (torch.log(mut_prob + 1e-10) - torch.log(wt_prob + 1e-10)).cpu().item()
                    
                    results.append({
                        "mutation": str(mutation),
                        "position": mutation.position,
                        "wt_aa": mutation.wt_aa,
                        "mut_aa": mutation.mut_aa,
                        "llr": llr,
                        "sensitivity": sensitivity
                    })
        
        return results

@st.cache_resource
def get_esm_scorer(model_name="esm2_t6_8M_UR50D", device=None):
    """获取ESM评分器实例（支持复用，使用Streamlit缓存）"""
    return ESMScorer(model_name=model_name, device=device)

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
    scorer = get_esm_scorer()
    return scorer.score_mutations(sequence, mutations, calculate_sensitivity)
