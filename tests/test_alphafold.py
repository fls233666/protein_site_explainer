import pytest
import requests.exceptions
from src.alphafold import AlphaFoldData


def test_alphafold_data_class():
    """测试AlphaFoldData类的功能"""
    # 创建AlphaFoldData对象
    test_data = AlphaFoldData(
        uniprot_id="P0DTC2",
        plddt_scores=[(i, 90.0) for i in range(1, 101)]  # 模拟100个位置的pLDDT分数
    )
    
    assert test_data.uniprot_id == "P0DTC2"
    assert len(test_data.plddt_scores) == 100


def test_get_plddt_at_position():
    """测试获取特定位置的pLDDT分数"""
    # 创建AlphaFoldData对象
    test_data = AlphaFoldData(
        uniprot_id="P0DTC2",
        plddt_scores=[(i, 90.0) for i in range(1, 101)]  # 模拟100个位置的pLDDT分数
    )
    
    # 测试存在的位置
    plddt_nterm = test_data.get_plddt_at_position(10)
    assert isinstance(plddt_nterm, float)
    assert 0 <= plddt_nterm <= 100
    assert plddt_nterm == 90.0
    
    plddt_cterm = test_data.get_plddt_at_position(100)
    assert isinstance(plddt_cterm, float)
    assert 0 <= plddt_cterm <= 100
    assert plddt_cterm == 90.0
    
    # 测试不存在的位置
    plddt_none = test_data.get_plddt_at_position(200)
    assert plddt_none is None
