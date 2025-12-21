import pytest
from src.parsing import parse_mutation, parse_mutation_list, validate_mutations, Mutation


def test_parse_mutation():
    """测试解析单个突变"""
    mutation = parse_mutation("A123T")
    assert mutation.wt_aa == "A"
    assert mutation.position == 123
    assert mutation.mut_aa == "T"
    assert str(mutation) == "A123T"


def test_parse_mutation_list():
    """测试解析突变列表"""
    mutations = parse_mutation_list("A123T, K456M, R789L")
    assert len(mutations) == 3
    assert [str(mut) for mut in mutations] == ["A123T", "K456M", "R789L"]


def test_parse_mutation_list_spaces():
    """测试用空格分隔的突变列表"""
    mutations = parse_mutation_list("A123T K456M R789L")
    assert len(mutations) == 3
    assert [str(mut) for mut in mutations] == ["A123T", "K456M", "R789L"]


def test_validate_mutations():
    """测试验证突变"""
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mutations = [Mutation("A", 1, "T"), Mutation("Z", 26, "A")]
    
    # 应该通过验证
    validate_mutations(mutations, sequence)
    
    # 错误的野生型氨基酸应该引发异常
    wrong_mutation = [Mutation("B", 1, "T")]
    with pytest.raises(ValueError):
        validate_mutations(wrong_mutation, sequence)
    
    # 超出范围的位置应该引发异常
    out_of_range = [Mutation("A", 99, "T")]
    with pytest.raises(ValueError):
        validate_mutations(out_of_range, sequence)


def test_invalid_mutation_format():
    """测试无效的突变格式"""
    with pytest.raises(ValueError):
        parse_mutation("123AT")  # 错误的顺序
    
    with pytest.raises(ValueError):
        parse_mutation("AA123T")  # 两个野生型氨基酸
        
    with pytest.raises(ValueError):
        parse_mutation("A123TT")  # 两个突变型氨基酸
        
    with pytest.raises(ValueError):
        parse_mutation("a123t")  # 小写字母
