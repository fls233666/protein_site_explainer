import pytest
import torch
from src.esm_scoring import ESMScorer, score_mutations
from src.parsing import parse_mutation_list

# 测试用序列
TEST_SEQUENCE = "ABCDEFGHIJKLMNOPQRST"

class TestESMScoring:
    """测试ESM打分功能"""
    
    @pytest.fixture
    def scorer(self):
        """创建ESM评分器实例"""
        return ESMScorer(model_name="esm2_t6_8M_UR50D", device="cpu")
    
    def test_standard_amino_acid_tokens(self, scorer):
        """测试标准氨基酸的token索引正确性"""
        # 20种标准氨基酸
        standard_amino_acids = "ACDEFGHIKLMNPQRSTVWY"
        
        for aa in standard_amino_acids:
            assert aa in scorer.alphabet.tok_to_idx, f"Standard amino acid '{aa}' not found in ESM alphabet"
            
            # 确保索引不是特殊token（如mask、start、stop等）
            idx = scorer.alphabet.tok_to_idx[aa]
            assert scorer.alphabet.get_tok(idx) == aa, f"Token mismatch for amino acid '{aa}': expected '{aa}', got '{scorer.alphabet.get_tok(idx)}'"
    
    def test_llr_calculation(self, scorer):
        """测试LLR计算的正确性"""
        # 简单测试序列和突变
        sequence = "AAAAA"
        
        # 测试单个突变
        llr = scorer.calculate_llr(sequence, 3, "A", "V")
        assert isinstance(llr, float), f"Expected float, got {type(llr)}"
        
        # 测试多个突变
        mutations = parse_mutation_list("A1V, A3V, A5V")
        results = scorer.score_mutations(sequence, mutations)
        
        assert len(results) == 3
        for result in results:
            assert "llr" in result
            assert "sensitivity" in result
            assert isinstance(result["llr"], float)
            assert isinstance(result["sensitivity"], float) or result["sensitivity"] is None
    
    def test_batch_processing(self, scorer):
        """测试批处理功能"""
        # 创建同一位置的多个突变
        sequence = "AAAAA"
        mutations = parse_mutation_list("A3V, A3L, A3I")
        
        # 批量计算
        results = scorer.score_mutations(sequence, mutations)
        
        # 验证结果
        assert len(results) == 3
        for result in results:
            assert result["position"] == 3
            assert result["wt_aa"] == "A"
            assert result["mut_aa"] in ["V", "L", "I"]
            assert "llr" in result
            assert "sensitivity" in result
    
    def test_sensitivity_calculation(self, scorer):
        """测试敏感度计算"""
        sequence = "AAAAA"
        
        # 计算位置3的敏感度
        sensitivity = scorer.calculate_sensitivity(sequence, 3, "A")
        assert isinstance(sensitivity, float), f"Expected float, got {type(sensitivity)}"
        
        # 验证批量计算时的敏感度
        mutations = parse_mutation_list("A1V, A3V")
        results = scorer.score_mutations(sequence, mutations, calculate_sensitivity=True)
        
        for result in results:
            assert "sensitivity" in result
            assert isinstance(result["sensitivity"], float)
    
    def test_non_standard_amino_acid(self, scorer):
        """测试非标准氨基酸的错误处理"""
        # 测试非标准氨基酸序列
        with pytest.raises(ValueError, match="Non-standard amino acid"):
            scorer.get_logits("AAXAA")
        
        # 测试非标准氨基酸突变
        sequence = "AAAAA"
        with pytest.raises(ValueError, match="Wildtype amino acid.*not a standard amino acid"):
            scorer.calculate_llr(sequence, 3, "X", "A")
        
        with pytest.raises(ValueError, match="Mutant amino acid.*not a standard amino acid"):
            scorer.calculate_llr(sequence, 3, "A", "X")
    
    def test_position_validation(self, scorer):
        """测试位置验证"""
        sequence = "AAAAA"
        
        # 测试无效位置
        with pytest.raises(ValueError, match="Position.*out of sequence bounds"):
            scorer.calculate_llr(sequence, 0, "A", "V")
        
        with pytest.raises(ValueError, match="Position.*out of sequence bounds"):
            scorer.calculate_llr(sequence, 10, "A", "V")
        
        # 测试氨基酸不匹配
        with pytest.raises(ValueError, match="Sequence at position.*expected wildtype"):
            scorer.calculate_llr(sequence, 3, "V", "A")
    
    def test_cache_decorator(self):
        """测试缓存装饰器"""
        sequence = "AAAAA"
        mutations = parse_mutation_list("A1V, A3V")
        
        # 第一次调用（应该计算）
        results1 = score_mutations(sequence, mutations)
        
        # 第二次调用（应该命中缓存）
        results2 = score_mutations(sequence, mutations)
        
        # 验证结果相同
        assert len(results1) == len(results2) == 2
        for r1, r2 in zip(results1, results2):
            assert r1["llr"] == r2["llr"]
            assert r1["sensitivity"] == r2["sensitivity"]

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_esm_scoring.py"])
