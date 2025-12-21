import pytest
import requests.exceptions
from src.uniprot import get_uniprot_entry, get_features_at_position


@pytest.mark.smoke
def test_get_uniprot_entry():
    """测试获取UniProt条目（smoke test）"""
    # 使用一个小的、已知的蛋白质
    entry = get_uniprot_entry("P00760")  # Trypsinogen
    assert entry.uniprot_id == "P00760"
    assert len(entry.sequence) > 0
    assert len(entry.features) > 0


@pytest.mark.smoke
def test_get_features_at_position():
    """测试获取特定位置的特征（smoke test）"""
    entry = get_uniprot_entry("P00760")
    features = get_features_at_position(entry.features, 1)
    assert isinstance(features, list)
    
    # 位置1应该是信号肽
    signal_peptide_features = [f for f in features if f.type == "signal peptide"]
    assert len(signal_peptide_features) > 0


@pytest.mark.smoke
def test_nonexistent_uniprot_id():
    """测试不存在的UniProt ID（smoke test）"""
    with pytest.raises(requests.exceptions.HTTPError):
        get_uniprot_entry("NONEXISTENT123")
